import { Injectable } from '@angular/core';
import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';
import { SessionService } from '../auth/session.service';

@Injectable()
export class ApiInterceptor implements HttpInterceptor {
  constructor(private readonly session: SessionService) {}
  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    const token = this.session.token;
    return next.handle(token ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : request);
  }
}

