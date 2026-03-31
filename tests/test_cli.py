from typer.testing import CliRunner
from marketing_persona_counsel.cli import app
import os

runner = CliRunner()

def test_list_personas_empty_vault(tmp_path):
    # Set vault path to empty dir
    env = os.environ.copy()
    env["OBSIDIAN_VAULT_PATH"] = str(tmp_path)
    
    result = runner.invoke(app, ["--list-personas"], env=env)
    assert result.exit_code == 1
    # Check stderr if available, or try to find it in stdout if click handles it
    assert "No marketing personas found" in (result.stdout + (result.stderr if hasattr(result, "stderr") else ""))


def test_cli_no_llm_markdown(tmp_path):
    vault = tmp_path / "vault"
    brand_dir = vault / "personas" / "brand"
    brand_dir.mkdir(parents=True)
    
    persona_file = brand_dir / "Patty.md"
    persona_file.write_text("# Patty\n**Archetype:** Dev\n## System Prompt Seed\n> Hi", encoding="utf-8")
    
    post_file = tmp_path / "post.md"
    post_file.write_text("---\ntitle: Test\n---\nContent", encoding="utf-8")
    
    env = os.environ.copy()
    env["OBSIDIAN_VAULT_PATH"] = str(vault)
    
    # Run CLI
    result = runner.invoke(app, [str(post_file), "--no-llm", "--dry-run"], env=env)
    assert result.exit_code == 0
    assert "Council Evaluation: Test" in result.stdout
    assert "Patty" in result.stdout
