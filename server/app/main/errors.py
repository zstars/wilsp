from . import main


@main.app_errorhandler(404)
def page_not_found(e):
    return "Page not found"
