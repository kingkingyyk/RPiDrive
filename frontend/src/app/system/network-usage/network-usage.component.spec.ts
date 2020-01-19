import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { NetworkUsageComponent } from './network-usage.component';

describe('NetworkUsageComponent', () => {
  let component: NetworkUsageComponent;
  let fixture: ComponentFixture<NetworkUsageComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ NetworkUsageComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NetworkUsageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
