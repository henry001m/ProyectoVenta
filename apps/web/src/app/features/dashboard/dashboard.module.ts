import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CardModule } from 'primeng/card';
import { MessageModule } from 'primeng/message';
import { DashboardComponent } from './dashboard.component';

@NgModule({ declarations: [DashboardComponent], imports: [CommonModule, CardModule, MessageModule, RouterModule.forChild([{ path: '', component: DashboardComponent }])] })
export class DashboardModule {}

