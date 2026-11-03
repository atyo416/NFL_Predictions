"""M5 orchestration keeps raw data season-bounded and existing callers modern-only."""
from pathlib import Path
import json
import pandas as pd
from .history_data import update_history,audit_history,load_history
from .history_features import reconstruct,attach_elo
from .history_analysis import run
from .integrity import atomic_json


def execute(command,data,root,start=1999,end=2017,refresh=False,protocol=None):
    data=Path(data);root=Path(root)
    if command=='update-history':update_history(data,start,end,refresh);return
    audit=audit_history(data,root/'reports/history_audit')
    if command=='audit-history':
        print(pd.read_csv(root/'reports/history_audit/source_audit.csv').to_string(index=False));return
    config=json.loads(Path(protocol or root/'config/m5_protocol.json').read_text())
    if refresh:config['rebuild_revision']=pd.Timestamp.now(tz='UTC').isoformat()
    s,m=load_history(data)
    frame,feature_audit=reconstruct(s,m,data/'history_features')
    frame=attach_elo(frame,s,config['elo'])
    # Reconstruct the actual original history, not an expanded-history W1 proxy.
    from .data_loader import cached
    modern_s,modern_m=cached(data=data)
    from .m4_features import prepare
    m4config=json.loads((root/'config/m4_protocol.json').read_text())
    reference=prepare(modern_s,modern_m,m4config,data/'features')
    provenance={'source_manifests':{p.stem:json.loads(p.read_text()) for p in (data/'manifests').glob('*.json')},'historical_audit':str(root/'reports/history_audit/source_audit.csv')}
    result=run(frame,reference,root/'reports/m5',root/'models/registry',config,provenance,feature_audit)
    print(result)
    if command=='report-m5':
        from .history_report import engineering_report
        print(engineering_report(result,root))
