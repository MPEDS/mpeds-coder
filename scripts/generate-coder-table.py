from context import models
from context import export

export.exportAnnotations(models.CodeEventCreator, 'coder-table')

