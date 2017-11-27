interface HTMLAudioElement {
    mozSetup(channels: number, rate: number);
    mozWriteAudio(data: any);
}

declare var webkitAudioContext: {
    prototype: AudioContext;
    new (): AudioContext;
}
