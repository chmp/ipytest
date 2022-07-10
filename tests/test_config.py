import ipytest


def test_autoconfig(scoped_config, mock_ipython):
    ipytest.autoconfig()
    config = ipytest.config()

    assert config["rewrite_asserts"] is True
    assert config["magics"] is True
    assert config["defopts"] == "auto"


def test_config_rewrite_asserts(scoped_config, mock_ipython):
    ipytest.config(rewrite_asserts=True)
    assert len(mock_ipython.ast_transformers) == 1

    ipytest.config(rewrite_asserts=False)
    assert len(mock_ipython.ast_transformers) == 0
