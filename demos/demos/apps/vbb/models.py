# File: models.py

from django.db import models
from django.core import urlresolvers

from demos.common.utils import config, crypto, enums, fields


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
		return urlresolvers.reverse('vbb:', args=[self.id])
	
	class Meta:
		ordering = ['id']
	
	class ElectionManager(models.Manager):
		def get_by_natural_key(self, id):
			return self.get(id=id)
	
	objects = ElectionManager()
	
	def natural_key(self):
		return (self.id,)


class Ballot(models.Model):
	
	election = models.ForeignKey(Election)
	
	serial = models.PositiveIntegerField()
	credential_hash = models.CharField(max_length=128)
	
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
	
	security_code_hash = models.CharField(max_length=128)
	security_code = models.CharField(max_length=config.SECURITY_CODE_LEN,
		blank=True, default='')
	
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


class Question(models.Model):
	
	election = models.ForeignKey(Election)
	m2m_parts = models.ManyToManyField(Part)
	
	text = models.CharField(max_length=config.TEXT_LEN)
	index = models.PositiveSmallIntegerField()
	
	columns = models.PositiveSmallIntegerField()
	choices = models.PositiveSmallIntegerField()
	
	# Other model methods and meta options
	
	def __str__(self):
		return "%s. %s" % (self.index + 1, self.text)
	
	class Meta:
		ordering = ['election', 'index']
		unique_together = ('election', 'index')
	
	class QuestionManager(models.Manager):
		def get_by_natural_key(self, index, id):
			return self.get(index=index, election__id=id)
	
	objects = QuestionManager()
	
	def natural_key(self):
		return (self.index,) + self.election.natural_key()


class OptionV(models.Model):
	
	part = models.ForeignKey(Part)
	question = models.ForeignKey(Question)
	
	votecode = models.CharField(max_length=config.VOTECODE_LEN)
	receipt = models.CharField(max_length=config.RECEIPT_LEN)
	
	voted = models.BooleanField(default=False)
	index = models.PositiveSmallIntegerField()
	
	# Other model methods and meta options
	
	def __str__(self):
		return "%s - %s" % (self.index + 1, self.votecode)
	
	class Meta:
		ordering = ['part', 'question', 'index']
		unique_together = ('part', 'question', 'votecode')
	
	class OptionVManager(models.Manager):
		def get_by_natural_key(self, votecode, index, tag, serial, id):
			return self.get(votecode=votecode, part__ballot__serial=serial,
				question__index=index, question__election__id=id,
				part__tag=tag, part__ballot__election__id=id)
	
	objects = OptionVManager()
	
	def natural_key(self):
		return (self.votecode,) + \
			self.question.natural_key()[:-1] + self.part.natural_key()


class OptionC(models.Model):
	
	question = models.ForeignKey(Question)
	
	text = models.CharField(max_length=config.TEXT_LEN)
	index = models.PositiveSmallIntegerField()
	
	# Other model methods and meta options
	
	def __str__(self):
		return "%s. %s" % (self.index + 1, self.text)
	
	class Meta:
		ordering = ['question', 'index']
		unique_together = ('question', 'text')
	
	class OptionCManager(models.Manager):
		def get_by_natural_key(self, text, index, id):
			return self.get(text=text, question__index=index,
				question__election__id=id)
	
	objects = OptionCManager()
	
	def natural_key(self):
		return (self.text,) + self.question.natural_key()


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

