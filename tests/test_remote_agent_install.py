from pathlib import Path


INSTALL = Path(__file__).parents[1] / "deploy" / "remote-agent" / "install.sh"


def test_install_script_prepares_agent_evidence_directory_with_service_ownership():
    text = INSTALL.read_text(encoding="utf-8")

    assert "install -d -o logistics-agent -g logistics-agent /var/lib/logistics-agent" in text
    assert "install -d -o logistics-agent -g logistics-agent -m 0750 /var/lib/logistics-agent/evidence" in text


def test_install_script_does_not_require_agent_to_create_system_evidence_directory():
    text = INSTALL.read_text(encoding="utf-8")
    evidence_create = "install -d -o logistics-agent -g logistics-agent -m 0750 /var/lib/logistics-agent/evidence"

    assert evidence_create in text
    assert "LOGISTICS_CGROUP_EVIDENCE_PATH" not in text


def test_install_script_preserves_read_write_path_for_evidence_store():
    text = INSTALL.read_text(encoding="utf-8")

    assert "ReadWritePaths=$AGENT_DIR /var/lib/logistics-agent $REPO_DIR" in text
