import pytest
from pytk.filters.docker import DockerFilter

@pytest.fixture
def f():
    return DockerFilter()

def test_matches_docker(f):
    assert f.matches(["docker", "ps"])
    assert f.matches(["docker-compose", "up"])
    assert not f.matches(["git", "status"])

def test_docker_ps_compressed(f):
    raw = (
        "CONTAINER ID   IMAGE         COMMAND   CREATED       STATUS        PORTS     NAMES\n"
        "a1b2c3d4e5f6   nginx:latest  \"/docker\"  2 hours ago   Up 2 hours    80/tcp    web_1\n"
        "b2c3d4e5f6a1   redis:7       \"redis\"    1 hour ago    Up 1 hour     6379/tcp  cache_1\n"
    )
    out = f.filter(raw, ["docker", "ps"])
    assert "web_1" in out
    assert "nginx:latest" in out
    assert "Up 2 hours" in out
    assert "CONTAINER ID" not in out
    assert "COMMAND" not in out

def test_docker_images_compressed(f):
    raw = (
        "REPOSITORY    TAG       IMAGE ID       CREATED        SIZE\n"
        "nginx         latest    abc123def456   2 days ago     142MB\n"
        "redis         7         def456abc123   1 week ago     117MB\n"
    )
    out = f.filter(raw, ["docker", "images"])
    assert "nginx:latest" in out
    assert "redis:7" in out
    assert "IMAGE ID" not in out
    assert "SIZE" not in out

def test_docker_logs_truncates(f):
    lines = [f"log line {i}" for i in range(200)]
    raw = "\n".join(lines)
    out = f.filter(raw, ["docker", "logs", "web_1"])
    result_lines = out.splitlines()
    assert len(result_lines) <= 100
    assert "log line 199" in out  # last lines kept

def test_docker_logs_strips_ansi(f):
    raw = "\x1b[32mGreen text\x1b[0m\nNormal line"
    out = f.filter(raw, ["docker", "logs", "web_1"])
    assert "\x1b" not in out
    assert "Green text" in out

def test_docker_logs_deduplicates(f):
    lines = ["repeated line"] * 20 + ["unique line"]
    raw = "\n".join(lines)
    out = f.filter(raw, ["docker", "logs", "web_1"])
    assert "repeated" in out
    assert "[repeated" in out
    count = out.count("repeated line\n") + (1 if out.endswith("repeated line") else 0)
    assert count < 20

def test_docker_build_strips_steps(f):
    raw = (
        "Sending build context to Docker daemon  10MB\n"
        "Step 1/5 : FROM python:3.11\n"
        "---> Using cache\n"
        "Step 2/5 : COPY . /app\n"
        "---> Running in abc123\n"
        "Step 3/5 : RUN pip install -r requirements.txt\n"
        "---> Running in def456\n"
        "Successfully built abc123def456\n"
        "Successfully tagged myapp:latest\n"
    )
    out = f.filter(raw, ["docker", "build", "."])
    assert "Step" not in out
    assert "Using cache" not in out
    assert "Successfully built" in out

def test_docker_build_keeps_errors(f):
    raw = (
        "Step 1/3 : FROM python:3.11\n"
        "---> Using cache\n"
        "Step 2/3 : RUN pip install broken-package\n"
        "ERROR: Could not find a version that satisfies the requirement broken-package\n"
        "The command '/bin/sh -c pip install broken-package' returned a non-zero code: 1\n"
    )
    out = f.filter(raw, ["docker", "build", "."])
    assert "ERROR" in out or "error" in out.lower()

def test_docker_compose_up_compressed(f):
    raw = (
        "Pulling db (postgres:14)...\n"
        "abc123: Pull complete\n"
        "Creating myapp_db_1 ... done\n"
        "Creating myapp_web_1 ... done\n"
    )
    out = f.filter(raw, ["docker", "compose", "up"])
    assert "myapp_db_1" in out
    assert "myapp_web_1" in out
    assert "Pull complete" not in out

def test_docker_compose_via_compose_cmd(f):
    raw = "Creating myapp_web_1 ... done\n"
    out = f.filter(raw, ["docker-compose", "up"])
    assert "myapp_web_1" in out


def test_docker_inspect_compresses_json():
    import json
    from pytk.filters.docker import DockerFilter
    f = DockerFilter()
    sample = json.dumps([{'Id': 'abc123def456789', 'Name': '/mycontainer', 'State': {'Status': 'running', 'Pid': 1234}, 'Config': {'Image': 'nginx:latest'}, 'NetworkSettings': {'Ports': {'80/tcp': [{'HostPort': '8080'}]}}, 'Mounts': [{'Type': 'bind', 'Source': '/data'}]}])
    result = f.filter(sample, ['docker', 'inspect', 'mycontainer'])
    assert 'abc123def456' in result
    assert 'nginx:latest' in result
    assert 'running' in result
    assert len(result) < len(sample)
