import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { SessionService } from '@/core/auth/session.service';

@Component({ selector: 'ki-root', standalone: false, template: '<router-outlet></router-outlet>' })
export class AppComponent { constructor(public readonly session: SessionService, private readonly router: Router) {} logout(): void { this.session.clear(); void this.router.navigate(['/auth/login']); } }

