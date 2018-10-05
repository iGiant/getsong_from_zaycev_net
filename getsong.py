from sys import argv
from requests import get, head
from lxml import html
from os.path import exists
from fake_useragent import UserAgent
from mutagen.id3 import ID3, TIT2, TALB, COMM


def get_num(value: str)-> tuple:
    if '-' in value:
        begin, end = value.split('-')
        if not begin:
            begin = '1'
        if not end:
            end = '-1'
        return begin, end
    elif value.isdigit():
        return value, value
    return '-1', '-1'


def get_song(*args, **kwargs):
    begin = int(kwargs.get('count', ('1', '1'))[0])
    end = int(kwargs.get('count', ('1', '1'))[1])
    url_base = "http://zaycev.net"
    url_add = ''
    ua = UserAgent()
    header = {
        'User-Agent':
            ua.random}
    param = None
    if args:
        url_add = "search.html"
        query = '+'.join(args)
        param = {"query_search": query}
    http = get(f'{url_base}/{url_add}', headers=header, params=param)
    response = html.fromstring(http.text)
    links = response.xpath('//div[@data-rbt-content-id]/@data-url')
    artists = response.xpath('//*[@itemprop="byArtist"]/a/text()')
    songs = response.xpath('//*[@itemprop="name"]/a/text()')
    list_out = begin == -1 and end == -1
    begin = max(begin, 1)
    if end == -1 or end > len(songs):
        end = len(songs)
    begin = min(begin, end)
    if list_out:
        print('Доступные композиции:')
    if links:
        shift = 0
        i = begin
        while i <= end + shift:
            url = get(f'{url_base}{links[i-1]}').json()['url']
            presence = head(url)
            if presence.status_code != 200 and presence.headers.get('Content-Type') != 'audio/mpeg':
                i += 1
                shift += 1
                continue
            title = f'{artists[i-1].strip()} – {songs[i-1].strip()}.mp3'
            size = round(int(presence.headers.get('Content-Length', '0')) / 1048576, 1)
            if list_out:
                print(f'{i + 1 - begin - shift}. {title} ({size} Мб)')
            else:
                while exists(title):
                    title = '_' + title
                number = '' if begin == end else f"{i + 1 - begin - shift}."
                print(f"Загружается: {number}{title}", end='', flush=True)
                song = get(url, stream=True)
                with open(title, 'wb') as file:
                    for index, chunk in enumerate(song.iter_content(1048576)):
                        text = f"\rЗагружается: {number}{title}{'.' * (index % 4)}"
                        print(f"\r{' ' * (len(text) + 2)}", end='', flush=True)
                        print(text, end='', flush=True)
                        file.write(chunk)
                audio = ID3(title)
                song_name = audio['TIT2'][0][:-13]
                audio.add(TIT2(text=song_name))
                audio.add(TALB(text=''))
                audio.add(COMM(lang='eng', text=''))
                audio.save()
                print(f"\rЗагружено: {number}{title}     ")
            i += 1
    else:
        exit(2)


if __name__ == '__main__':
    if len(argv) > 1:
        if '=' in argv[-1]:
            get_song(*argv[1:-1], count=get_num(argv[-1].split('=')[-1]))
        else:
            get_song(*argv[1:], count=('1', '1'))
    else:
        get_song(*'', count=get_num('l',))
