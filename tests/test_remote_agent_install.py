from pathlib import Path


INSTALL = Path(__file__).parents[1] / "deploy" / "remote-agent" / "install.sh"


def test_install_script_prepares_agent_evidence_directory_with_service_ownership():
    text = INSTALL.read_text(encoding="utf-8")

    assert "install -d -o logistics-agent -g logistics-agent /var/lib/logistics-agent" in text
    assert "install -d -o logistics-agent -g logistics-agent -m 0750 /var/lib/logistics-agent/evidence" in text


def test_install_script_keeps_cgroup_rehearsal_opt_in():
    text = INSTALL.read_text(encoding="utf-8")

    assert "cgroup_rehearsal.py" not in text
    assert "cgroup_gate.py" not in text
    assert "LOGISTICS_CGROUP_REHEARSAL=1" not in text


def test_install_script_preserves_read_write_path_for_evidence_store():
    text = INSTALL.read_text(encoding="utf-8")

    assert "ReadWritePaths=$AGENT_DIR /var/lib/logistics-agent $REPO_DIR" in text


def test_install_script_keeps_credentials_out_of_repository_paths():
    text = INSTALL.read_text(encoding="utf-8")

    assert "EnvironmentFile=$ENV_DIR/agent.env" in text
    assert "0600" in text
    assert "AGENT_AUTH_TOKEN" in text
    assert "AI_GATEWAY_API_KEY" in text
