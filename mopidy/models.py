from copy import copy

class ImmutableObject(object):
    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return super(ImmutableObject, self).__setattr__(name, value)
        raise AttributeError('Object is immutable.')

class Artist(ImmutableObject):
    """
    :param uri: artist URI
    :type uri: string
    :param name: artist name
    :type name: string
    """

    #: The artist URI. Read-only.
    uri = None

    #: The artist name. Read-only.
    name = None


class Album(ImmutableObject):
    """
    :param uri: album URI
    :type uri: string
    :param name: album name
    :type name: string
    :param artists: album artists
    :type artists: list of :class:`Artist`
    :param num_tracks: number of tracks in album
    :type num_tracks: integer
    """

    #: The album URI. Read-only.
    uri = None

    #: The album name. Read-only.
    name = None

    #: The number of tracks in the album. Read-only.
    num_tracks = 0

    def __init__(self, *args, **kwargs):
        self._artists = kwargs.pop('artists', [])
        super(Album, self).__init__(*args, **kwargs)

    @property
    def artists(self):
        """List of :class:`Artist` elements. Read-only."""
        return copy(self._artists)


class Track(ImmutableObject):
    """
    :param uri: track URI
    :type uri: string
    :param title: track title
    :type title: string
    :param artists: track artists
    :type artists: list of :class:`Artist`
    :param album: track album
    :type album: :class:`Album`
    :param track_no: track number in album
    :type track_no: integer
    :param date: track release date
    :type date: :class:`datetime.date`
    :param length: track length in milliseconds
    :type length: integer
    :param bitrate: bitrate in kbit/s
    :type bitrate: integer
    :param id: track ID (unique and non-changing as long as the process lives)
    :type id: integer
    """

    #: The track URI. Read-only.
    uri = None

    #: The track title. Read-only.
    title = None

    #: The track :class:`Album`. Read-only.
    album = None

    #: The track number in album. Read-only.
    track_no = 0

    #: The track release date. Read-only.
    date = None

    #: The track length in milliseconds. Read-only.
    length = None

    #: The track's bitrate in kbit/s. Read-only.
    bitrate = None

    #: The track ID. Read-only.
    id = None

    def __init__(self, *args, **kwargs):
        self._artists = kwargs.pop('artists', [])
        super(Track, self).__init__(*args, **kwargs)

    @property
    def artists(self):
        """List of :class:`Artist`. Read-only."""
        return copy(self._artists)

    def mpd_format(self, position=0, search_result=False):
        """
        Format track for output to MPD client.

        :param position: track's position in playlist
        :type position: integer
        :rtype: list of two-tuples
        """
        result = [
            ('file', self.uri or ''),
            ('Time', self.length and (self.length // 1000) or 0),
            ('Artist', self.mpd_format_artists()),
            ('Title', self.title or ''),
            ('Album', self.album and self.album.name or ''),
            ('Date', self.date or ''),
        ]
        if self.album is not None and self.album.num_tracks != 0:
            result.append(('Track', '%d/%d' % (
                self.track_no, self.album.num_tracks)))
        else:
            result.append(('Track', self.track_no))
        if not search_result:
            result.append(('Pos', position))
            result.append(('Id', self.id or position))
        return result

    def mpd_format_artists(self):
        """
        Format track artists for output to MPD client.

        :rtype: string
        """
        return u', '.join([a.name for a in self.artists])


class Playlist(ImmutableObject):
    """
        :param uri: playlist URI
        :type uri: string
        :param name: playlist name
        :type name: string
        :param tracks: playlist's tracks
        :type tracks: list of :class:`Track` elements
    """

    #: The playlist URI. Read-only.
    uri = None

    #: The playlist name. Read-only.
    name = None

    def __init__(self, *args, **kwargs):
        self._tracks = kwargs.pop('tracks', [])
        super(Playlist, self).__init__(*args, **kwargs)

    @property
    def tracks(self):
        """List of :class:`Track` elements. Read-only."""
        return copy(self._tracks)

    @property
    def length(self):
        """The number of tracks in the playlist. Read-only."""
        return len(self._tracks)

    def mpd_format(self, start=0, end=None, search_result=False):
        """
        Format playlist for output to MPD client.

        Optionally limit output to the slice ``[start:end]`` of the playlist.

        :param start: position of first track to include in output
        :type start: int
        :param end: position after last track to include in output
        :type end: int or :class:`None` for end of list
        :rtype: list of lists of two-tuples
        """
        if end is None:
            end = self.length
        tracks = []
        for track, position in zip(self.tracks[start:end], range(start, end)):
            tracks.append(track.mpd_format(position, search_result))
        return tracks

    def with_(self, uri=None, name=None, tracks=None):
        """
        Create a new playlist object with the given values. The values that are
        not given are taken from the object the method is called on.

        Does not change the object on which it is called.

        :param uri: playlist URI
        :type uri: string
        :param name: playlist name
        :type name: string
        :param tracks: playlist's tracks
        :type tracks: list of :class:`Track` elements
        :rtype: :class:`Playlist`
        """
        if uri is None:
            uri = self.uri
        if name is None:
            name = self.name
        if tracks is None:
            tracks = self.tracks
        return Playlist(uri=uri, name=name, tracks=tracks)
