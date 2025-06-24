from pathlib import Path

DOIT_CONFIG = {"default_tasks": ['html']}


def task_pot():
    """Build pot"""
    return {
        'actions': ["pybabel extract . -o Bot/TG_bot.pot"],
        'file_dep': [str(i) for i in Path("./Bot").glob("*.py")],
        'targets': ["Bot/TG_bot.pot"],
    }


def task_po():
    """Build po"""
    return {
        'actions': ["pybabel update -D TG_bot -i Bot/TG_bot.pot -l en_US -d Bot/locales"],
        'file_dep': ['Bot/TG_bot.pot'],
        'targets': ["Bot/locales/en_US/TG_bot.po"],
    }


def task_il8n():
    """Build il8n"""
    return {
            "file_dep": ["Bot/locales/en_US/LC_MESSAGES/TG_bot.po"],
            "actions": ["pybabel compile -D TG_bot -d Bot/locales"],
            "targets": ['Bot/locales/en_US/LC_MESSAGES/TG_bot.mo']
    }


def task_html():
    """Build html"""
    return {
            "file_dep": [str(i) for i in Path("./source").glob("*.rst")],
            'task_dep': ['test'],
            "actions": ["sphinx-build -M html doc doc/_build"],
            'targets': ['doc/_build/html/index.html'],
    }


def task_test():
    """Run tests"""
    return {
            'task_dep': ['il8n'],
            "actions": ["LANG=ru_RU.UTF-8 LC_ALL=ru_RU.UTF-8 pytest ./tests/test_handlers.py"],
    }


def task_erase():
    """Clean represitory"""
    return {
            'actions': ['git clean -xdf'],
    }


def task_sdist():
    """Make sdist"""
    return {
            'task_dep': ['html', 'erase'],
            'actions': ['python3 -m build -s -n']
    }


def task_wheel():
    """Make wheel"""
    return {
            'task_dep': ['html'],
            'actions': ['python3 -m build -w']
    }

