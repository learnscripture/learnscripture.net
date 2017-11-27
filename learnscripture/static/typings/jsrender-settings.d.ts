// jsrender '$.views.settings.delimiters' interface that is not in most recent
// https://github.com/DefinitelyTyped/DefinitelyTyped definition
// at time of writing

declare namespace JsRender {
    interface Settings {
        delimiters(): string[];
        delimiters(delims: string[]): Settings;
        delimiters(openChars: string, closeChars: string): Settings;
        delimiters(openChars: string, closeChars: string, link: string): Settings;
    }

    interface Views {
        settings: Settings;
    }
}
