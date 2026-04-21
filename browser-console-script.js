/* Don't copy links manually. Open the desired YouTube playlist in browser, press F12, go to the Console tab, and paste this: */

const ids = Array.from(document.querySelectorAll('ytd-playlist-video-renderer a#video-title'))
              .map(link => new URL(link.href).searchParams.get('v'))
              .filter(id => id !== null);
console.log(JSON.stringify(ids));