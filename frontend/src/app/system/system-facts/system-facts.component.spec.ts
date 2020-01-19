import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SystemFactsComponent } from './system-facts.component';

describe('SystemFactsComponent', () => {
  let component: SystemFactsComponent;
  let fixture: ComponentFixture<SystemFactsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SystemFactsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SystemFactsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
