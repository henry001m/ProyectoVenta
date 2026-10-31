import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { WhatsAppComponent } from './whatsapp.component';

const routes: Routes = [{ path: '', component: WhatsAppComponent }];

@NgModule({ imports: [RouterModule.forChild(routes)], exports: [RouterModule] })
export class WhatsAppRoutingModule {}
