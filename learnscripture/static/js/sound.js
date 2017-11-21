"use strict";
var $ = require('jquery');

var isSetup = false;
var audioContext = null;
var useAudio = false;
var useMozSetup = false;

var setUpAudio = function () {
    if (isSetup) {
        return;
    }

    if (typeof AudioContext !== 'undefined') {
        audioContext = new AudioContext();
    } else if (typeof webkitAudioContext !== 'undefined') {
        audioContext = new webkitAudioContext();
    } else if (typeof Audio !== 'undefined') {
        useAudio = true;
        var test = new Audio();
        if (test.mozSetup !== undefined) {
            useMozSetup = true;
        }
    }
    isSetup = true;
};

var mozAudioBeep = function (frequency, length) {
    var audio = new Audio();
    // Set up a mono channel at 44.1Khz
    var sampleRate = 44100;
    audio.mozSetup(1, sampleRate);

    // Create a sample buffer array
    var samples = new Float32Array(Math.floor(sampleRate / 2 * length));
    var g = 2 * Math.PI * frequency / sampleRate;

    // Fill the sample buffer array with values
    for(var i=0; i<samples.length; i++){
        samples[i] = Math.sin(g * i)
    }
    audio.mozWriteAudio(samples);
}

var dataUriAudioBeep = function (frequency, length) {
	var output = "RIFF";
    var sampleRate = 44100;
    output+=str_from_dword(sampleRate * 2 * length+36);
	output+="WAVE";
	output+="fmt ";
	output+=str_from_dword(16);
	output+=str_from_word(1);
	output+=str_from_word(1);
	output+=str_from_dword(sampleRate);
	output+=str_from_dword(sampleRate * 2);
	output+=str_from_word(4);
	output+=str_from_word(16);
	output+="data";
	output+=str_from_dword(sampleRate * 2 * length);
    var g = 2 * Math.PI * frequency / sampleRate;
	for (var i = 0; i < sampleRate * length; i++) {
        var val = Math.round(Math.sin(i * g)*32760)
		output+=str_from_word(val);
	}
	var audio = new Audio();
    audio.src = "data:audio/x-wav;base64," + encode64(output);
	audio.play();
}

var keyStr = "ABCDEFGHIJKLMNOP" +
    "QRSTUVWXYZabcdef" +
    "ghijklmnopqrstuv" +
    "wxyz0123456789+/" +
    "=";

function encode64(input) {
    var output = "";
    var chr1, chr2, chr3 = "";
    var enc1, enc2, enc3, enc4 = "";
    var i = 0;

    do {
        chr1 = input.charCodeAt(i++);
        chr2 = input.charCodeAt(i++);
        chr3 = input.charCodeAt(i++);

        enc1 = chr1 >> 2;
        enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
        enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
        enc4 = chr3 & 63;

        if (isNaN(chr2)) {
            enc3 = enc4 = 64;
        } else if (isNaN(chr3)) {
            enc4 = 64;
        }

        output = output +
            keyStr.charAt(enc1) +
            keyStr.charAt(enc2) +
            keyStr.charAt(enc3) +
            keyStr.charAt(enc4);
        chr1 = chr2 = chr3 = "";
        enc1 = enc2 = enc3 = enc4 = "";
    } while (i < input.length);

    return output;
}

function str_from_dword(dw)
{
	return String.fromCharCode(dw&0xFF,dw>>8&0xFF,dw>>16&0xFF,dw>>24&0xFF);
}

function str_from_word(w)
{
	return String.fromCharCode(w&0xFF,w>>8&0xFF);
}

function str_from_byte(b)
{
	return String.fromCharCode(b&0xFF);
}

var audioContextBeep = function(frequency, length) {
    var source = audioContext.createOscillator();
    source.frequency.value = frequency;
    source.connect(audioContext.destination);
    if (source.noteOn != undefined) {
        source.noteOn(0);
        source.noteOff(audioContext.currentTime + length);
    } else if (source.start != undefined) {
        source.start(0);
        source.stop(audioContext.currentTime + length);
    }
}

var doBeep = function (frequency, length) {
    try {
        if (useAudio) {
            if (useMozSetup) {
                mozAudioBeep(frequency, length);
            } else {
                dataUriAudioBeep(frequency, length);
            }
        } else if (audioContext != null) {
            audioContextBeep(frequency, length);
        }
    } catch (e) {
        // ignore
    }
}


// === Exports ===
exports.setUpAudio = setUpAudio;
exports.doBeep = doBeep;

