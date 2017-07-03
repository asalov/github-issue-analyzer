from django.apps import AppConfig
from .data import IssueAnalyzer

class AnalyzerConfig(AppConfig):
    name = 'analyzer'
    analyzer = IssueAnalyzer()