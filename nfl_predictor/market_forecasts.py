"""Read actual saved forecasts and resolve exact artifacts, without model training."""
from pathlib import Path
import json
import sqlite3
import pandas as pd
from .model import load
from .registry import load_candidate,VERSION
from .ensemble import timestamp
from .ensemble_forecasts import records,probabilities
from .ensemble_registry import load_ensemble
from .integrity import digest
from .odds_store import key,append,utc_now

FAMILIES=['official_logistic','boosting','ensemble']


class ForecastRepository:
    def __init__(self,root,data):self.root=Path(root);self.data=Path(data);self.artifacts={};self.issues=[]

    def artifact(self,version):
        if not isinstance(version,str) or not VERSION.fullmatch(version):raise ValueError('Unsafe forecast artifact version')
        if version in self.artifacts:return self.artifacts[version]
        production=self.root/'models/production.joblib'
        if production.exists():
            model=load(production)
            if model['version']==version:
                result=(model,str(production),digest(production));self.artifacts[version]=result;return result
        candidate=self.root/'models/registry/candidates'/version
        if candidate.exists():
            model,metadata=load_candidate(self.root/'models/registry',version)
            result=(model,str(candidate/'model.joblib'),metadata['artifact_sha256']);self.artifacts[version]=result;return result
        raise ValueError(f'Exact forecast artifact unavailable: {version}')

    def validate(self,record):
        created=timestamp(record['created_at']);cutoff=timestamp(record['data_cutoff']);kickoff=timestamp(record['kickoff'])
        if not cutoff<=created<kickoff:raise ValueError('Saved forecast has invalid creation/information/kickoff timestamps')
        model,path,sha=self.artifact(record['model_version'])
        if timestamp(model['training_cutoff'])>=cutoff:raise ValueError('Artifact training overlaps saved forecast cutoff')
        if not 0<=float(record['home_probability'])<=1:raise ValueError('Invalid saved forecast probability')
        record.update(artifact_path=path,artifact_sha256=sha,training_cutoff=model['training_cutoff'])
        record['forecast_id']=key({k:v for k,v in record.items() if k!='forecast_id'})
        return record

    def read(self):
        result=[];database=self.data/'predictions.db'
        if database.exists():
            db=sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)
            try:official=db.execute('SELECT id,payload,official FROM predictions ORDER BY id').fetchall()
            finally:db.close()
            for identifier,payload,official_flag in official:
                try:
                    f=json.loads(payload)
                    record={k:f[k] for k in ['game_id','home_team','away_team','kickoff','created_at','data_cutoff','model_version','home_probability']}
                    record.update(model='official_logistic',classification='genuine_saved_forecast',source_reference=f'official_sqlite:predictions/{identifier}',source_designation='official_original' if official_flag else 'champion_revision',source_fingerprint=key(f))
                    model,_,_=self.artifact(record['model_version'])
                    if 'logisticregression' not in getattr(model['pipeline'],'named_steps',{}):raise ValueError('Saved champion is not the M2 logistic architecture')
                    result.append(self.validate(record))
                except (KeyError,ValueError,FileNotFoundError) as exc:self.issues.append({'source':f'official_sqlite/{identifier}','reason':str(exc)})
        protocol=self.root/'config/m8_protocol.json'
        pinned=json.loads(protocol.read_text()).get('frozen_m7_policy','E1_equal__raw') if protocol.exists() else 'E1_equal__raw'
        for f in records(self.data/'m7/experimental_forecasts'):
            if f.get('ensemble_method')!=pinned:
                self.issues.append({'source':f['forecast_id'],'reason':'M7 method differs from the M8 frozen policy; no automatic reselection'})
                continue
            for family,probability,version in [('boosting',f['base_probabilities']['boosting'],f['base_versions']['boosting']),('ensemble',f['home_probability'],f['ensemble_version'])]:
                try:
                    record={k:f[k] for k in ['game_id','home_team','away_team','kickoff','created_at','data_cutoff']}
                    record.update(model=family,model_version=version,home_probability=probability,classification='genuine_saved_forecast',source_reference='M7_ledger:'+f['forecast_id'],source_designation='experimental_M5_architecture_annual_refit' if family=='boosting' else 'experimental_M7',source_fingerprint=key(f))
                    validated=self.validate(record)
                    expected=f['base_checksums']['boosting'] if family=='boosting' else None
                    if expected and validated['artifact_sha256']!=expected:raise ValueError('Saved M7 base checksum does not match its referenced artifact')
                    result.append(validated)
                except (KeyError,ValueError,FileNotFoundError) as exc:self.issues.append({'source':f['forecast_id'],'model':family,'reason':str(exc)})
        return result


def persist_forecasts(db,forecasts):
    with db:
        for f in forecasts:append(db,'forecasts',f,f['forecast_id'])


def historical_inference(root,schedules,metrics,game_id,decision,db):
    """Frozen M7 annual artifacts, new decision-cutoff features; never issue a forecast."""
    root=Path(root);decision=timestamp(decision)
    pointer=root/'reports/m7/latest.json'
    if not pointer.exists():raise ValueError('M7 frozen historical artifacts are unavailable')
    run=pointer.parent/json.loads(pointer.read_text())['run'];checks=json.loads((run/'outputs.json').read_text())
    if any(digest(run/p)!=sha for p,sha in checks.items()):raise ValueError('M7 historical report integrity failure')
    g=schedules[schedules.game_id.eq(game_id)].iloc[0];year=int(g.season)
    if year not in [2024,2025]:raise ValueError('M8 historical inference is explicitly limited to exploratory 2024–2025')
    method=json.loads((run/'selection.json').read_text())['method'];found=None
    pinned=json.loads((root/'config/m8_protocol.json').read_text())['frozen_m7_policy']
    if method!=pinned:raise ValueError('M8 frozen M7 policy differs from the selected research report; no automatic reselection')
    for version in json.loads((run/'registry_versions.json').read_text()):
        if not version.startswith(f'm7-ensemble-{year}-'):continue
        descriptor=json.loads((root/'models/registry/candidates'/version/'metadata.json').read_text())
        params=descriptor['parameters']
        if params['method']+'__'+params['calibration_method']==method:found=version;break
    if found is None:raise ValueError('Frozen selected M7 historical policy is unavailable')
    model,bases,_=load_ensemble(root/'models/registry',found)
    s=schedules.copy();mask=s.game_id.eq(game_id)
    s.loc[mask,'completed']=False
    if 'status' in s:s.loc[mask,'status']='scheduled'
    config=json.loads((root/'config/m7_protocol.json').read_text())
    frame,source=probabilities(s,metrics,model,bases,config,decision,decision,game_id)
    if frame.empty:raise ValueError('Historical decision must strictly precede target kickoff')
    p=frame.iloc[0];created=timestamp(utc_now()).isoformat();result=[]
    for family,version,probability in [('official_logistic',model['base_refs']['logistic']['version'],p.p_logistic),('boosting',model['base_refs']['boosting']['version'],p.p_boosting),('ensemble',found,p.ensemble_probability)]:
        artifact=bases['logistic'] if family=='official_logistic' else bases['boosting'] if family=='boosting' else model
        artifact_path=root/'models/registry/candidates'/version/'model.joblib'
        record={'game_id':game_id,'home_team':g.home_team,'away_team':g.away_team,'kickoff':g.kickoff.isoformat(),'created_at':created,'data_cutoff':decision.isoformat(),'model':family,'model_version':version,'home_probability':float(probability),'classification':'retrospective_oos_inference','source_reference':str(run),'source_designation':'M2_architecture_OOS_refit_not_issued_champion_forecast' if family=='official_logistic' else 'retrospective_annual_refit','source_fingerprint':key(source),'artifact_sha256':digest(artifact_path),'artifact_path':str(artifact_path),'training_cutoff':artifact['training_cutoff']}
        record['forecast_id']=key({k:v for k,v in record.items() if k!='created_at'})
        with db:saved=append(db,'forecasts',record,record['forecast_id'],ignore_fields=['created_at'])
        result.append(saved)
    return result
