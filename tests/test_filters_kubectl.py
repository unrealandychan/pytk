import pytest
from pytk.filters.kubectl import KubectlFilter

f = KubectlFilter()


def test_matches_kubectl():
    assert f.matches(['kubectl', 'get', 'pods'])

def test_matches_k_alias():
    assert f.matches(['k', 'describe', 'pod/myapp'])

def test_no_match():
    assert not f.matches(['helm', 'install'])
    assert not f.matches([])


GET_PODS_WIDE = """\
NAME                          READY   STATUS    RESTARTS   AGE   IP           NODE         NOMINATED NODE   READINESS GATES
myapp-7d9f8b6c4-xk2pl         1/1     Running   0          2d    10.0.0.1     node-1       <none>           <none>
myapp-7d9f8b6c4-abc12         0/1     Pending   3          1h    <none>       node-2       <none>           <none>"""


def test_kubectl_get_pods_strips_columns():
    result = f.filter(GET_PODS_WIDE, ['kubectl', 'get', 'pods', '-o', 'wide'])
    assert 'NAME' in result
    assert 'STATUS' in result
    assert 'RESTARTS' in result
    assert 'AGE' in result
    assert 'IP' not in result
    assert 'NODE' not in result
    assert 'myapp-7d9f8b6c4-xk2pl' in result
    assert 'Running' in result


DESCRIBE_WITH_ANNOTATIONS = """\
Name:         myapp-pod
Namespace:    default
Annotations:  kubectl.kubernetes.io/last-applied-configuration: {"apiVersion":"v1"}
              some.other/annotation: value
Labels:       app=myapp
Status:       Running
Containers:
  myapp:
    Image: myapp:latest
Conditions:
  Ready   True"""


def test_kubectl_describe_strips_annotations():
    result = f.filter(DESCRIBE_WITH_ANNOTATIONS, ['kubectl', 'describe', 'pod', 'myapp-pod'])
    assert 'Annotations' not in result
    assert 'kubectl.kubernetes.io' not in result
    assert 'Name:' in result
    assert 'Status:' in result


DESCRIBE_WITH_WARNING = """\
Name:         myapp-pod
Namespace:    default
Status:       OOMKilled
Events:
  Type     Reason      Age   From     Message
  ----     ------      ---   ----     -------
  Warning  OOMKilled   1m    kubelet  Container exceeded memory limit"""


def test_kubectl_describe_keeps_warning_events():
    result = f.filter(DESCRIBE_WITH_WARNING, ['kubectl', 'describe', 'pod', 'myapp-pod'])
    assert 'Warning' in result
    assert 'OOMKilled' in result
    assert 'Events:' in result


DESCRIBE_NORMAL_ONLY = """\
Name:         myapp-pod
Namespace:    default
Status:       Running
Events:
  Type     Reason      Age   From       Message
  ----     ------      ---   ----       -------
  Normal   Scheduled   5m    scheduler  Successfully assigned default/myapp-pod to node-1
  Normal   Pulled      4m    kubelet    Container image already present"""


def test_kubectl_describe_strips_normal_events():
    result = f.filter(DESCRIBE_NORMAL_ONLY, ['kubectl', 'describe', 'pod', 'myapp-pod'])
    assert 'Events:' not in result
    assert 'Normal' not in result
    assert 'Name:' in result


def test_kubectl_logs_truncates():
    lines = [f'log line {i}' for i in range(200)]
    output = '\n'.join(lines)
    result = f.filter(output, ['kubectl', 'logs', 'mypod'])
    result_lines = result.splitlines()
    assert len(result_lines) == 100
    assert result_lines[0] == 'log line 100'


def test_kubectl_logs_strips_ansi():
    output = '\x1b[32mGREEN\x1b[0m normal'
    result = f.filter(output, ['kubectl', 'logs', 'mypod'])
    assert '\x1b' not in result
    assert 'GREEN' in result


def test_kubectl_logs_deduplicates():
    lines = ['same line'] * 10 + ['different']
    output = '\n'.join(lines)
    result = f.filter(output, ['kubectl', 'logs', 'mypod'])
    assert result.count('same line') == 1
    assert 'repeated' in result
    assert 'different' in result


EVENTS_TABLE = """\
LAST SEEN   TYPE      REASON      OBJECT         MESSAGE
5m          Normal    Scheduled   pod/myapp      assigned to node
3m          Warning   OOMKilled   pod/myapp      memory limit exceeded
1m          Normal    Pulled      pod/myapp      image pulled"""


def test_kubectl_events_warnings_only():
    result = f.filter(EVENTS_TABLE, ['kubectl', 'get', 'events'])
    assert 'Warning' in result
    assert 'OOMKilled' in result
    assert 'Normal' not in result
    assert 'LAST SEEN' in result  # header kept


def test_kubectl_apply_compact():
    output = 'deployment.apps/myapp configured\n\nservice/myapp unchanged\n'
    result = f.filter(output, ['kubectl', 'apply', '-f', 'manifest.yaml'])
    assert 'deployment.apps/myapp configured' in result
    assert 'service/myapp unchanged' in result
    # No empty lines
    for line in result.splitlines():
        assert line.strip()


def test_kubectl_rollout_last_line_only():
    output = 'Waiting for rollout to finish: 1 of 3 updated replicas are available...\nWaiting for rollout to finish: 2 of 3 updated replicas are available...\nsuccessfully rolled out'
    result = f.filter(output, ['kubectl', 'rollout', 'status', 'deploy/myapp'])
    assert result == 'successfully rolled out'
