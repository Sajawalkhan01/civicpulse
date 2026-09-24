// Mirrors the server-side constraints on ComplaintCreate (backend/app/domain/models.py)
// purely so the UI can fail fast with a helpful message. The server re-validates
// everything independently and is the actual authority -- this never decides
// category/priority, only whether text/location are long enough to submit.
export const TEXT_MIN = 10;
export const TEXT_MAX = 2000;
export const LOCATION_MIN = 3;
export const LOCATION_MAX = 200;

export interface ComplaintFormValues {
  text: string;
  location: string;
}

export interface ComplaintFormErrors {
  text?: string;
  location?: string;
}

export function validateComplaintForm(values: ComplaintFormValues): ComplaintFormErrors {
  const errors: ComplaintFormErrors = {};
  const text = values.text.trim();
  const location = values.location.trim();

  if (text.length < TEXT_MIN) {
    errors.text = `Please add a bit more detail — at least ${TEXT_MIN} characters (${text.length} so far).`;
  } else if (text.length > TEXT_MAX) {
    errors.text = `That's a lot of detail — please keep it under ${TEXT_MAX} characters (${text.length} so far).`;
  }

  if (location.length < LOCATION_MIN) {
    errors.location = `Location needs at least ${LOCATION_MIN} characters.`;
  } else if (location.length > LOCATION_MAX) {
    errors.location = `Location must be ${LOCATION_MAX} characters or fewer.`;
  }

  return errors;
}
