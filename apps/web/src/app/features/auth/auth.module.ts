import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { LoginComponent } from './components/login.component';

@NgModule({ declarations: [LoginComponent], imports: [CommonModule, FormsModule, ButtonModule, CardModule, InputTextModule, RouterModule.forChild([{ path: '', component: LoginComponent }])], exports: [LoginComponent] })
export class AuthModule {}

