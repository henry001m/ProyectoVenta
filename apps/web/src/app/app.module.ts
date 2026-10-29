import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';
import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { AuthenticatedLayoutComponent } from './layout/authenticated-layout.component';
import { ApiInterceptor } from '@/core/network/api.interceptor';
import { StoreModule } from '@ngrx/store';
import { sessionReducer } from './store/session.reducer';

@NgModule({ declarations: [AppComponent, AuthenticatedLayoutComponent], imports: [BrowserModule, HttpClientModule, ButtonModule, MessageModule, StoreModule.forRoot({ session: sessionReducer }), AppRoutingModule], providers: [{ provide: HTTP_INTERCEPTORS, useClass: ApiInterceptor, multi: true }], bootstrap: [AppComponent] })
export class AppModule {}

