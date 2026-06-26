"""Pruebas de los extractores específicos por tipo de módulo."""

from __future__ import annotations


def _module(workflow, name):
    return next(m for m in workflow.modules if m.name == name)


def test_param_extraction(workflow):
    params = _module(workflow, "Parametros").parameters
    assert len(params) == 1
    assert params[0].name == "Cliente"
    assert params[0].default == "ITAU"


def test_data_input_location_and_reader(workflow):
    mod = _module(workflow, "BasePortal")
    assert "base.txt" in mod.location
    assert mod.reader == "CSVSimpleDataReader"
    assert mod.extra["TextCodec"] == "ISO-8859-1"


def test_transformer_keeps_only_logic(workflow):
    transforms = _module(workflow, "Calcula").transformations
    # La transformación "SinLogica" (sin FCV) debe descartarse.
    assert len(transforms) == 2
    targets = {t.dot_name for t in transforms}
    assert "Records.SinLogica" not in targets


def test_script_fcv_parsed(workflow):
    transforms = _module(workflow, "Calcula").transformations
    script_t = next(t for t in transforms if t.fcv_type == "ScriptFCV")
    assert "return true" in script_t.script
    assert script_t.kind == "script"


def test_concat_fcv_summary(workflow):
    transforms = _module(workflow, "Calcula").transformations
    concat_t = next(t for t in transforms if t.fcv_type == "ConcatStrFCV")
    assert "pre='X-'" in concat_t.expression


def test_filter_extraction(workflow):
    flt = _module(workflow, "FiltraVariables").filter
    assert flt is not None
    assert flt.has_else_output is True
    assert flt.conditions[0].value == "Variables"
    assert "Equalto" in flt.as_expression()


def test_join_keys(workflow):
    mod = _module(workflow, "Cruce")
    assert mod.join_type == "StringSortAndSearcher"
    assert mod.join_keys[0].left == "Records.NumId"
    assert mod.join_keys[0].right == "Base.NumId"


def test_script_module(workflow):
    scripts = _module(workflow, "Hoja").scripts
    assert len(scripts) == 1
    assert "Records.NumId" in scripts[0].reads
    assert "Out" in scripts[0].writes


def test_renamer(workflow):
    renames = _module(workflow, "Renombra").renames
    assert ("Records.TipoId", "Tipo") in renames
