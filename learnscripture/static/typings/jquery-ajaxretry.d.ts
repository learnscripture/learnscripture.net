declare namespace JQuery {
    namespace Ajax {
        interface DelayFunc {
            (i: number): number;
        }

        interface TickFunc {
            (data: TickData): void;
        }

        interface RetryOptions {
            attempts?: number;
            cutoff?: number;
            delay_func?: DelayFunc;
            error_codes?: number[];
            slot_time?: number;
            tick?: TickFunc;
        }

        interface TickData extends RetryOptions {
            ticks: number;
        }

        interface AjaxSettingsBase<TContext> {
            retry?: RetryOptions;
        }
    }
}
