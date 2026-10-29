import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CardModule } from 'primeng/card';
import { SourcesComponent } from './sources.component';

@NgModule({ declarations: [SourcesComponent], imports: [CommonModule, CardModule, RouterModule.forChild([{ path: '', component: SourcesComponent }])] })
export class SourcesModule {}

