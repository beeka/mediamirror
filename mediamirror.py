#!/usr/bin/env python3
import os
import shutil
import sys
import platform
import subprocess
import time
import flac2mp3

# Set up logging
import logging
log = logging.getLogger("mediamirror")
log_formatter = logging.Formatter("%(asctime)s - %(message)s")
log_console = logging.StreamHandler()
log_console.setFormatter(log_formatter)
log.addHandler(log_console)

source_root = None
dest_root = None
dry_run = False

def create_directory_for_file(dest):
	destdir = os.path.dirname(dest)
	if not os.path.exists(destdir):
		log.info('Making directory: %s', destdir)
		if not dry_run:
			try:
				if platform.system() == 'Linux':
					# os.makedirs doesn't work well on Linux (over shares)
					proc = subprocess.Popen(['mkdir', '-p', destdir])
					proc.communicate()
					proc.wait()
					if proc.returncode != 0:
						log.error("There was an error calling mkdir -p")
					cwd = os.getcwd()
					os.chdir(destdir)
					os.chdir(cwd)
				else:
					os.makedirs(destdir, mode=0o775)
			except:
				# give the file system / network a couple of seconds to recognise the new directory
				time.sleep(2)
				if not os.path.exists(destdir):
					log.error('There was a problem creating directory %s: %s', destdir, sys.exc_info()[0])
					return False
				else:
					log.warning('A problem was reported when creating directory %s: %s', destdir, sys.exc_info()[0])
				#return False
	elif not os.path.isdir(destdir):
			log.error('%s exists but is not a directory!' % destdir)
			return False
	# give the file system / network a couple of seconds to recognise the new directory
	time.sleep(2)
	return os.path.exists(destdir)
	return True


def copy_file(source, dest):
	log.info('Copying file %s to %s', source, dest)
	if not create_directory_for_file(dest):
		return
	if not dry_run:
		shutil.copyfile(source, dest)


#from flac2mp3 import maybe_encode_file as flac_to_mp3
def flac_to_mp3(source, dest):
	log.info('Converting %s to %s' % (source, dest))
	if not create_directory_for_file(dest):
		return
	if not dry_run:
		from flac2mp3 import maybe_encode_file
		maybe_encode_file(source, dest)


def copy_playlist(source, dest):
	"""Copies m3u files, changing the any file paths within it to match
	the converted extentions."""
	log.info('Converting playlist %s to %s' % (source, dest))
	if not create_directory_for_file(dest):
		return
	if dry_run:
		return
	global conversions
	src = open(source)
	dest = open(dest, "w")
	for line in src:
		line = line.strip()
		for ext in list(conversions.keys()):
			if line.endswith(ext):
				(dest_ext, convert_fn) = conversions[ext]
				line = line.replace(source_root, dest_root)[:-len(ext)] + dest_ext
		print(line, file=dest)


#
# Setup the default behaviour for handling.
#
conversions = {
	'flac': ('mp3', flac_to_mp3),
	'mp3' : ('mp3', copy_file),
	'm4a' : ('m4a', copy_file),
	'jpg' : ('jpg', copy_file),
	'png' : ('png', copy_file),
	'm3u' : ('m3u', copy_playlist),
	}


def source_is_newer(source, dest):
	"""Returns True if the source path is newer than dest (or dest does not exist)."""
	if not os.path.exists(dest):
		# File is missing, so source is 'newer'
		return True
	else:
		# See if the source is newer than the dest
		source_mtime = os.path.getmtime(source)
		dest_mtime = os.path.getmtime(dest)
		return (source_mtime > dest_mtime)


def get_path_hierachy(path):
	s = set()
	s.add(path)
	(head, tail) = os.path.split(path)
	if len(tail) > 0:
		# There was a tail, so the head might still have something useful
		s |= get_path_hierachy(head)
	return s

# Maintain a list of all files that should be present in the mirror
# so we can figure out which ones to delete. NB: A set might be
# quicker than a list
mirrored = set()



def update_single_dir(directory):
	log.debug('Checking %s' % directory)
	global mirrored
	start_size = len(mirrored)

	# Find all files (not dirs) in this directory
	filenames = list()
	allnames = os.listdir(directory)
	for name in allnames:
		if not os.path.isdir(os.path.join(directory, name)):
			filenames.append(name)
	filenames.sort()

	# find all media files we are interested in
	for ext in list(conversions.keys()):
		(dest_ext, convert_fn) = conversions[ext]
		for filename in filenames:
			if not filename.endswith(ext):
				continue
			srcfilepath = os.path.join(directory, filename)
			dest = srcfilepath.replace(source_root, dest_root)[:-len(ext)] + dest_ext
			# Add to the list of files that should be in the mirror
			mirrored.add(dest)
			# See if we need to do anything? Basic check for the date here
			if source_is_newer(srcfilepath, dest):
				#log.debug('Newer file found: %s' % srcfilepath)
				convert_fn(srcfilepath, dest)

	# Add the destination directory hierachy to the list of things that are mirrored,
	# but only if an item was added to the list of valid mirrored files.
	if len(mirrored) > start_size:
		dest_directory = directory.replace(source_root, dest_root)
		mirrored |= get_path_hierachy(dest_directory)

# Exclude .@__thumb
excluded_paths = [ ".@__thumb", "_fresh" ]

def isWanted(path):
	for pattern in excluded_paths:
		if pattern in path:
			log.debug('Ignoring path: %s' % path)
			return False
	return True;

def dirwalk(dir):
	"""walk a directory tree returning each directory, using a generator"""
	yield dir
	for f in sorted( os.listdir(dir) ):
		fullpath = os.path.join(dir,f)
		if os.path.isdir(fullpath) and not os.path.islink(fullpath):
			for x in dirwalk(fullpath):  # recurse into subdir
				if isWanted(x):
					yield x


#
# Implement the command-line functionality
#
def main():
	from optparse import OptionParser

	usage = ("Usage: %prog [options]\n" +
			"\n" +
			"Mirrors media files from a HD/Lossless source directory to a " +
			"lossy-compressed destination directory (e.g. for portable media devices). " +
			"The behaviour is hard-coded to convert flac files to 192 VBR mp3, " +
			"copy wav, m4a, mp3, jpg, png and ignore the rest.")

	parser = OptionParser(usage=usage, version="%prog v0.1")
	parser.add_option("-d", "--dest", dest="destdir",
#					  default="X:/music/mp3s/from_flac",
					  help="The root of the destination media tree.")
	parser.add_option("-s", "--source", dest="sourcedir",
#					  default="Y:/music",
					  help="The root of the source media tree.")
	parser.add_option("-n", "--dry-run", dest="dryrun", action="store_true",
					  default=False,
					  help="Don't make any changes, just show what would happen.")
	parser.add_option("-p", "--prune", dest="prune", action="store_true",
					  default=False,
					  help="Remove old files from the destination that no longer have counterparts in the source.")
	parser.add_option("-v", "--verbose", dest="debug",
					  action="store_true", default=False,
					  help="Print more information for debugging purposes")
	parser.add_option("--flac", dest="flac", help="The flac executable to use.",
#	                  default="C:/Program Files (x86)/FLAC/flac.exe"
	                  )
	parser.add_option("--lame", dest="lame", help="The lame executable to use.",
#	                  default="C:/Program Files/Lame/lame.exe"
					  )
	(options, args) = parser.parse_args()

	if options.debug:
		log.setLevel(logging.DEBUG)
		flac2mp3.log.setLevel(logging.DEBUG)
	else:
		log.setLevel(logging.INFO)
		flac2mp3.log.setLevel(logging.INFO)

	# Read the options into the global variables
	global source_root, dest_root, flac, lame, dry_run
	source_root = options.sourcedir
	dest_root = options.destdir
	dry_run = options.dryrun
	if dry_run:
		log.info('Performing a dry-run of what would happen.')
	if options.flac != None:
		log.info("Setting FLAC decoder to %s", options.flac)
		flac2mp3.flac_exe = options.flac
	if options.lame != None:
		log.info("Setting LAME encoder to %s", options.lame)
		flac2mp3.lame_exe = options.lame

	#
	# Check for required 'options'
	#
	if source_root == None:
		parser.error("Source root must be specified.")

	if dest_root == None:
		parser.error("Destination root must be specified.")

	# The path mangling doesn't work well if path separator is missing
	if source_root[-1:] != os.sep:
		source_root = source_root + os.sep
	if dest_root[-1:] != os.sep:
			dest_root = dest_root + os.sep

	#
	# Check all directories that lie under the source root
	#
	log.info('Starting to mirror from %s to %s' % (source_root, dest_root))
	for x in dirwalk(source_root):
		update_single_dir(x)

	#
	# Prune directories/files in the dest that shouldn't be there
	#
	if options.prune:
		log.info('Pruning to remove old/unwanted files')
		to_prune = set()
		for dirname, dirnames, filenames in os.walk(dest_root):
			for subdirname in dirnames:
				dirpath = os.path.join(dirname, subdirname)
				if dirpath not in mirrored:
					parents = get_path_hierachy(dirpath)
					if len(to_prune & parents) == 0:
						log.debug('Will prune directory: %s' % dirpath)
						to_prune.add(dirpath)
			for filename in filenames:
				filepath = os.path.join(dirname, filename)
				if filepath not in mirrored:
					parents = get_path_hierachy(filepath)
					if len(to_prune & parents) == 0:
						log.debug('Will prune file: %s' % filepath)
						to_prune.add(filepath)

		for path in to_prune:
			log.info('Deleting: %s' % path)
			if os.path.isdir(path):
				if not dry_run:
					try:
						shutil.rmtree(path)
					except:
						log.error('Error deleting tree %s' % path)
			else:
				if not dry_run:
					try:
						os.remove(path)
					except:
						log.error('Error deleting file %s' % path)

if __name__ == "__main__":
	main()
