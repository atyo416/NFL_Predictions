"""Explicit historical research and separate prospective issuance commands."""
from pathlib import Path
import json
import pandas as pd
from .history_data import load_history
from .ensemble_data import build_matrix
from .ensemble_analysis import run


def execute(command,data,root,protocol=None,cutoff=None,game_id=None):
    root=Path(root);data=Path(data)
    config=json.loads(Path(protocol or root/'config/m7_protocol.json').read_text())
    schedules,metrics=load_history(data)
    if command=='grade-ensemble':
        from .ensemble_forecasts import grade,prospective_summary
        events=grade(schedules,data/'m7/experimental_forecasts');print(json.dumps({'events':len(events),**prospective_summary(data/'m7/experimental_forecasts')},indent=2));return
    if command=='forecast-ensemble':
        from .ensemble_forecasts import issue
        pointer=root/'reports/m7/latest.json'
        if not pointer.exists():raise ValueError('Run compare-m7 first; no versioned experimental ensemble is available')
        run_directory=pointer.parent/json.loads(pointer.read_text())['run']
        checks=json.loads((run_directory/'outputs.json').read_text())
        from .integrity import digest
        if any(digest(run_directory/p)!=sha for p,sha in checks.items()):raise ValueError('M7 report integrity failure')
        live=json.loads((run_directory/'prospective_model.json').read_text())
        print(issue(schedules,metrics,root/'models/registry',live['version'],config,data/'m7/experimental_forecasts',cutoff,game_id).to_string(index=False));return
    if cutoff is not None:raise ValueError('--cutoff is for genuine forecast-ensemble issuance; historical folds have fixed cutoffs')
    frame,directory=build_matrix(schedules,metrics,data,root,config);print(directory)
    if command=='build-ensemble-predictions':return
    meta=json.loads((directory/'metadata.json').read_text())
    result=run(frame,meta,root/'reports/m7',root/'models/registry',config);print(result)
    if command=='report-m7':
        from .ensemble_report import engineering_report
        print(engineering_report(result,root))
