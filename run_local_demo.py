import yaml
from orchestrator import Orchestrator
import asyncio, os, json

if __name__ == "__main__":
    with open('config.yaml') as f:
        cfg = yaml.safe_load(f)
    orch = Orchestrator(cfg)
    topic = "Kubernetes pod autoscaling best practices"
    result = orch.create_post(topic, {"publish": False, "tone": "technical"})
    if asyncio.iscoroutine(result):
        res = asyncio.run(result)
    else:
        res = result

    os.makedirs('examples', exist_ok=True)
    fname = os.path.join('examples', res['trace_id'] + '.json')
    with open(fname, 'w') as f:
        json.dump(res, f, indent=2)
    print("Saved:", fname)
