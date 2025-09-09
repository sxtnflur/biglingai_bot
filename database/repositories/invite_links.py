from .base import BaseRepo
from .. import models


class InviteLinksRepo(BaseRepo[models.InviteLink]):
    model = models.InviteLink