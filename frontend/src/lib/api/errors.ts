export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class UnauthorizedError extends ApiError {
  constructor(message = "Unauthorized", data?: unknown) {
    super(401, message, data);
    this.name = "UnauthorizedError";
  }
}

export class ForbiddenError extends ApiError {
  constructor(message = "Forbidden", data?: unknown) {
    super(403, message, data);
    this.name = "ForbiddenError";
  }
}

export class NotFoundError extends ApiError {
  constructor(message = "Not Found", data?: unknown) {
    super(404, message, data);
    this.name = "NotFoundError";
  }
}

export class ValidationError extends ApiError {
  constructor(message = "Validation Error", data?: unknown) {
    super(422, message, data);
    this.name = "ValidationError";
  }
}

export class ServerError extends ApiError {
  constructor(message = "Internal Server Error", data?: unknown) {
    super(500, message, data);
    this.name = "ServerError";
  }
}
