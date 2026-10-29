import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { TextareaModule } from 'primeng/textarea';
import { TableModule } from 'primeng/table';
import { ObservationsComponent } from './observations.component';

@NgModule({ declarations: [ObservationsComponent], imports: [CommonModule, FormsModule, ButtonModule, TextareaModule, TableModule, RouterModule.forChild([{ path: '', component: ObservationsComponent }, { path: 'new', component: ObservationsComponent }])] })
export class ObservationsModule {}

