# File: models.py

from django.db import models
from django.core import urlresolvers

from demos.common.utils import config, crypto, enums, fields, storage


class Config(models.Model):
	
	key = models.CharField(max_length=128, unique=True)
	value = models.CharField(max_length=128)
	
	# Other model methods and meta options
	
	def __str__(self):
		return "%s - %s" % (self.key, self.value)
	
	class ConfigManager(models.Manager):
		def get_by_natural_key(self, key):
			return self.get(key=key)
	
	objects = ConfigManager()
	
	def natural_key(self):
		return (self.key,)


class Election(models.Model):
	
	id = fields.Base32Field(primary_key=True)
	
	title = models.CharField(max_length=config.TEXT_LEN)
	ballots = models.PositiveIntegerField()
	
	start_datetime = models.DateTimeField()
	end_datetime = models.DateTimeField()
	
	state = fields.IntEnumField(cls=enums.State)
	
	# Other model methods and meta options
	
	def __str__(self):
		return "%s - %s" % (self.id, self.title)
	
	def get_absolute_url(self):
		return urlresolvers.reverse('bds:', args=[self.id])
	
	class Meta:
		ordering = ['id']
	
	class ElectionManager(models.Manager):
		def get_by_natural_key(self, id):
			return self.get(id=id)
	
	objects = ElectionManager()
	
	def natural_key(self):
		return (self.id,)


class Ballot(models.Model):
	
	fs = storage.TarFileStorage()
	
	def get_upload_file_path(self, filename):
		return "%s/%s" % (self.election.id, filename)
	
	election = models.ForeignKey(Election)
	
	serial = models.PositiveIntegerField()
	pdf = models.FileField(upload_to=get_upload_file_path, storage=fs)
	
	# Other model methods and meta options
	
	def __str__(self):
		return "%s" % self.serial
	
	class Meta:
		ordering = ['election', 'serial']
		unique_together = ('election', 'serial')
	
	class BallotManager(models.Manager):
		def get_by_natural_key(self, serial, id):
			return self.get(serial=serial, election__id=id)
	
	objects = BallotManager()
	
	def natural_key(self):
		return (self.serial,) + self.election.natural_key()


class Part(models.Model):
	
	ballot = models.ForeignKey(Ballot)
	
	tag = models.CharField(max_length=1, choices=(('A', 'A'), ('B', 'B')))
	
	vote_token = models.TextField()
	security_code = models.CharField(max_length=config.SECURITY_CODE_LEN)
	
	# Other model methods and meta options
	
	def __str__(self):
		return "%s" % self.tag
	
	class Meta:
		ordering = ['ballot', 'tag']
		unique_together = ('ballot', 'tag')
	
	class PartManager(models.Manager):
		def get_by_natural_key(self, tag, serial, id):
			return self.get(tag=tag, ballot__serial=serial,
				ballot__election__id=id)
	
	objects = PartManager()
	
	def natural_key(self):
		return (self.tag,) + self.ballot.natural_key()


class Trustee(models.Model):
	
	election = models.ForeignKey(Election)
	
	email = models.EmailField()
	
	# Other model methods and meta options
	
	def __str__(self):
		return "%s" % self.email
	
	class Meta:
		unique_together = ('election', 'email')
	
	class TrusteeManager(models.Manager):
		def get_by_natural_key(self, email, id):
			return self.get(election__id=id, email=email)
	
	objects = TrusteeManager()
	
	def natural_key(self):
		return (self.email,) + self.election.natural_key()


class RemoteUser(models.Model):
	
	username = models.CharField(max_length=128, unique=True)
	password = models.CharField(max_length=128)
	
	# Other model methods and meta options
	
	def __str__(self):
		return "%s - %s" % (self.username, self.password)
	
	class RemoteUserManager(models.Manager):
		def get_by_natural_key(self, username):
			return self.get(username=username)
	
	objects = RemoteUserManager()
	
	def natural_key(self):
		return (self.username,)


class Task(models.Model):
	
	task_id = models.UUIDField()
	election_id = fields.Base32Field(unique=True)

