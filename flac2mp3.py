#!/usr/bin/env python3

# Set up logging
import logging
log = logging.getLogger("flac2mp3")
log_formatter = logging.Formatter("%(asctime)s - %(message)s")
log_console = logging.StreamHandler()
log_console.setFormatter(log_formatter)
log.addHandler(log_console)

flac_exe = 'flac'
lame_exe = 'lame'

from mutagen.id3 import ID3, ID3NoHeaderError, TALB, TPE1, TPE2, TBPM, COMM, TCMP, TCOM, TPE3, TDRC, TPOS, TCON, TSRC, TEXT, TPUB, TIT2, TRCK, UFID, TXXX, TSOP, TSO2, APIC, TSOT, TSOA
from mutagen.flac import FLAC
import string
import sys
import os.path
from subprocess import Popen, PIPE

def one_to_one_conversion(flac_frame_name, frame_class):
    return (flac_frame_name, lambda mp3, flac: mp3.text[0] == flac, lambda str:[frame_class(encoding=3, text=str)])

def one_to_one_conversion_txxx(flac_frame_name, desc):
    return (flac_frame_name, lambda mp3, flac: mp3.text[0] == flac, lambda str:[TXXX(encoding=3, desc=desc, text=str)])

# Check http://picard-docs.musicbrainz.org/en/technical/tag_mapping.html for mappings used by Picard
mp3_flac_dict = {
    'TDRC':                             ('$DATE', lambda mp3, flac: mp3.text[0].text == flac, lambda value: [TDRC(encoding=3, text=value)]),
    'UFID:http://musicbrainz.org':      ('$MUSICBRAINZ_TRACKID', lambda mp3, flac: mp3.data.decode('ascii') == flac, lambda value: [UFID(encoding=3, owner='http://musicbrainz.org', data=value.encode('ascii'))]),
    'TALB':                             one_to_one_conversion('$ALBUM', TALB),
    'TPE1':                             one_to_one_conversion('$ARTIST', TPE1),
    'TPE2':                             one_to_one_conversion('$ALBUMARTIST', TPE2),
    'TBPM':                             one_to_one_conversion('$BPM', TBPM),
    'COMM':                             one_to_one_conversion('$COMMENT', COMM),
    'TCMP':                             one_to_one_conversion('$COMPILATION', TCMP),
    'TCOM':                             one_to_one_conversion('$COMPOSER', TCOM),
    'TPE3':                             one_to_one_conversion('$CONDUCTOR', TPE3),
    'TPOS':                             one_to_one_conversion('$DISCNUMBER/$TOTALDISCS', TPOS),
    'TCON':                             one_to_one_conversion('$GENRE', TCON),
    'TSRC':                             one_to_one_conversion('$ISRC', TSRC),
    'TEXT':                             one_to_one_conversion('$LYRICIST', TEXT),
    'TPUB':                             one_to_one_conversion('$PUBLISHER', TPUB),
    'TIT2':                             one_to_one_conversion('$TITLE', TIT2),
    'TRCK':                             one_to_one_conversion('$TRACKNUMBER/$TOTALTRACKS', TRCK),
    'TSOP':                             one_to_one_conversion('$ARTISTSORT', TSOP),
    'TSO2':                             one_to_one_conversion('$ALBUMARTISTSORT', TSO2),
    'TSOT':                             one_to_one_conversion('$TITLESORT', TSOT),
    'TSOA':                             one_to_one_conversion('$ALBUMSORT', TSOA),
    'TXXX:MusicBrainz Album Id':        one_to_one_conversion_txxx('$MUSICBRAINZ_ALBUMID', 'MusicBrainz Album Id'),
    'TXXX:MusicBrainz Album Status':    one_to_one_conversion_txxx('$MUSICBRAINZ_ALBUMSTATUS', 'MusicBrainz Album Status'),
    'TXXX:MusicBrainz Album Artist Id': one_to_one_conversion_txxx('$MUSICBRAINZ_ALBUMARTISTID', 'MusicBrainz Album Artist Id'),
    'TXXX:MusicBrainz Album Type':      one_to_one_conversion_txxx('$MUSICBRAINZ_ALBUMTYPE', 'MusicBrainz Album Type'),
    'TXXX:MusicBrainz Artist Id':       one_to_one_conversion_txxx('$MUSICBRAINZ_ARTISTID', 'MusicBrainz Artist Id'),
    'TXXX:MusicBrainz Release Group Id': one_to_one_conversion_txxx('$MUSICBRAINZ_RELEASEGROUPID', 'MusicBrainz Release Group Id'),
    'TXXX:MusicBrainz Release Track Id': one_to_one_conversion_txxx('$MUSICBRAINZ_RELEASETRACKID', 'MusicBrainz Release Track Id'),
    'TXXX:MusicBrainz Sortname':        one_to_one_conversion_txxx('$MUSICBRAINZ_SORTNAME', 'MusicBrainz Sortname'),
    'TXXX:MusicBrainz TRM Id':          one_to_one_conversion_txxx('$MUSICBRAINZ_TRMID', 'MusicBrainz TRM Id'),
    'TXXX:MD5':                         one_to_one_conversion_txxx('$MD5', 'MD5'),
    'TXXX:ALBUMARTISTSORT':             one_to_one_conversion_txxx('$ALBUMARTISTSORT', 'ALBUMARTISTSORT'),
}

status_printed=False

def flac_tag_dict(flac):
    ret = {}
    for key in list(flac.tags.as_dict().keys()):
        ret[key.upper()] = flac.tags[key][0]
    ret['MD5'] = ('%x' % flac.info.md5_signature)
    if 'TRACKTOTAL' in ret:
        ret['TOTALTRACKS'] = ret['TRACKTOTAL']
    if 'DISCTOTAL' in ret:
        ret['TOTALDISCS'] = ret['DISCTOTAL']
    if 'TOTALTRACKS' not in ret:
        ret['TOTALTRACKS'] = ''
    if 'TOTALDISCS' not in ret:
        ret['TOTALDISCS'] = ''
    return ret

def encode_file(flac_name, mp3_name):
    # We need to pass --tl (or any tag option) to ensure Mutagen can read the file afterwards.
    flac_cmd = [flac_exe, "--decode", "--silent", "--stdout", flac_name]
    flac = Popen(flac_cmd, stdout=PIPE)
    lame_cmd = [lame_exe, "--vbr-new", "-V2", "--quiet", "--noreplaygain", "--tl", "placeholder", "-", mp3_name]
    lame = Popen(lame_cmd, stdin=flac.stdout)
    log.debug("Transcoding command: %s | %s", str(flac_cmd), str(lame_cmd))
    lame.communicate()
    lame.wait()
    flac.wait()
    if flac.returncode != 0 or lame.returncode != 0:
        log.error("There was a problem transcoding the file.\n%s returned %d\n%s returned %d",
                  str(flac_cmd), flac.returncode, str(lame_cmd), lame.returncode);
        return False
    return True

def print_status(file_name, pos, status):
    global status_printed
    if not status_printed:
        print(file_name)
        for i in range(pos):
            sys.stdout.write(" ")
        status_printed = True
    sys.stdout.write(status)
    sys.stdout.flush

def maybe_encode_file(flac_name, mp3_name):
    if os.path.isfile(mp3_name):
        if os.path.getmtime(mp3_name) >= os.path.getmtime(flac_name):
            return
        # Need to check md5 to make sure they're the same:
        flac = FLAC(flac_name)
        mp3 = ID3(mp3_name)
        try:
            if (len(mp3.getall('TXXX:MD5')) == 0) or ('%x' % flac.info.md5_signature) != mp3['TXXX:MD5'].text[0]:
                try:
                    mp3_sig = mp3['TXXX:MD5'].text[0]
                except KeyError:
                    mp3_sig = 'None'
                print_status(mp3_name, 0, "R")
                if not encode_file(flac_name, mp3_name):
                    return
        except ID3NoHeaderError:
            print_status(mp3_name, 0, "I")
            encode_file(flac_name, mp3_name)
    else:
        print_status(mp3_name, 0, "E")
        encode_file(flac_name, mp3_name)
    tag_sync(flac_name, mp3_name)

def tag_sync(flac_name, mp3_name):
    mp3 = ID3(mp3_name)
    flac = FLAC(flac_name)

    flactags = flac_tag_dict(flac)
    log.debug("Source tags present: %s", '; '.join(sorted(flactags.keys())))
    log.debug("Destination tags present: %s", '; '.join(sorted(mp3.keys())))
    tag_differences = {}
    tag_index = 1

    # First, check whether the tags that can easily be translated match:
    for frame in list(mp3_flac_dict.keys()):
        mp3_has_frame = True
        flac_has_frame = True
        frames_differ = False
        mp3_value = None
        flac_value = None

        format, comparator, id3_generator = mp3_flac_dict[frame]

        try:
            mp3_value = mp3[frame]
        except KeyError:
            mp3_has_frame = False

        try:
            flac_value = string.Template(format).substitute(flactags)
        except KeyError:
            flac_has_frame = False

        if flac_has_frame and mp3_has_frame:
            frames_differ = not comparator(mp3_value, flac_value)

        if (flac_has_frame and not mp3_has_frame) or frames_differ:
            log.debug("%s differs: %s <> %s", frame, flac_value, mp3_value)
            tag_differences[frame] = id3_generator(flac_value)
            print_status(mp3_name, tag_index, ".")
        elif not flac_has_frame and mp3_has_frame:
            tag_differences[frame] = None
            print_status(mp3_name, tag_index, "X")
        else:
            print_status(mp3_name, tag_index, " ")
        tag_index += 1

    # Now, check pictures:
    for picture in flac.pictures:
        have_picture = False

        for apic in mp3.getall('APIC'):
            if apic.mime == picture.mime and apic.type == picture.type and apic.data == picture.data:
                have_picture = True
        if not have_picture:
            if 'APIC:' not in tag_differences:
                tag_differences['APIC:'] = []
            tag_differences['APIC:'].append(APIC(encoding=3, desc='', type=picture.type, data=picture.data, mime=picture.mime))
            print_status(mp3_name, tag_index, "P")
    print("")
    # And now push the changed tags to the MP3.
    for frame in list(tag_differences.keys()):
        if tag_differences[frame] == None:
            mp3.delall(frame)
        else:
            mp3.setall(frame, tag_differences[frame])

    if len(list(tag_differences.keys())) > 0:
        mp3.save(mp3_name, v1=1)
    else:
        os.utime(mp3_name, None)


if __name__ == "__main__":
    maybe_encode_file(sys.argv[1], sys.argv[2])
