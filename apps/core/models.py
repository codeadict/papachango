# -*- coding: utf-8 -*-
# Copyright (C) 2013 Kruger Labs
# Developer: Dairon Medina Caro <daironm@kruger.com.ec>
from django.db import models
from django.utils.translation import gettext as _
from base import filesystem

import caching.base

# Our apps should subclass ManagerBase instead of models.Manager for caching
ManagerBase = caching.base.CachingManager


def determine_image_upload_path(instance, filename):
    return "images/%(partition)d/%(filename)s" % {
        'partition': filesystem.get_partition_id(instance.pk),
        'filename': filesystem.safe_filename(filename),
    }

class KModel(models.Model):
    """
    Base Model for apps with caching support
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = ManagerBase()
    uncached = models.Manager()

    class Meta:
        abstract = True
        get_latest_by = 'created'


    def update(self, **kw):
        """
        Shortcut for doing an UPDATE on this object.

        If _signal=False is in ``kw`` the post_save signal won't be sent.
        """
        signal = kw.pop('_signal', True)
        cls = self.__class__
        for k, v in kw.items():
            setattr(self, k, v)
        if signal:
            # Detect any attribute changes during pre_save and add those to the
            # update kwargs.
            attrs = dict(self.__dict__)
            models.signals.pre_save.send(sender=cls, instance=self)
            for k, v in self.__dict__.items():
                if attrs[k] != v:
                    kw[k] = v
                    setattr(self, k, v)
        cls.objects.filter(pk=self.pk).update(**kw)
        if signal:
            models.signals.post_save.send(sender=cls, instance=self,
                                          created=False)

