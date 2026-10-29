import { createAction, props } from '@ngrx/store';

export const sessionLoaded = createAction('[Session] Loaded', props<{ userId: number; role: string }>());
export const sessionCleared = createAction('[Session] Cleared');

