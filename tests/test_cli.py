"""Pruebas de la interfaz de línea de comandos."""

from __future__ import annotations

from inspire.cli.main import main


def test_cli_stats_only(sample_xml_path, capsys):
    code = main([str(sample_xml_path), "--stats-only"])
    assert code == 0
    out = capsys.readouterr().out
    assert "Módulos" in out


def test_cli_generates_json(sample_xml_path, tmp_path):
    out_dir = tmp_path / "out"
    code = main([str(sample_xml_path), "-o", str(out_dir), "-f", "json"])
    assert code == 0
    assert (out_dir / "sample.json").exists()


def test_cli_missing_file(tmp_path):
    code = main([str(tmp_path / "nope.xml")])
    assert code == 2
