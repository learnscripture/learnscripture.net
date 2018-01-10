/// <reference path="../typings/audiocontext-extra.d.ts" />

var context: AudioContext | null = null;

const RAMP_VALUE = 0.00001;

export const setUpAudio = function() {
    if (context != null) {
        return;
    }

    if (typeof AudioContext !== 'undefined') {
        context = new AudioContext();
    }
};


export const doBeep = function(frequency, duration) {
    setUpAudio();
    if (context == null) {
        return;
    }
    var currentTime = context.currentTime;
    var osc = context.createOscillator();
    var gain = context.createGain();

    osc.connect(gain);
    gain.connect(context.destination);

    gain.gain.setValueAtTime(gain.gain.value, currentTime);
    gain.gain.exponentialRampToValueAtTime(RAMP_VALUE, currentTime + duration);

    osc.onended = function() {
        gain.disconnect(context.destination);
        osc.disconnect(gain);
    };

    osc.type = 'sine';
    osc.frequency.value = frequency;
    osc.start(currentTime);
    osc.stop(currentTime + duration);
}
