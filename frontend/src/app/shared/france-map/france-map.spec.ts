import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FranceMap } from './france-map';

describe('FranceMap', () => {
  let component: FranceMap;
  let fixture: ComponentFixture<FranceMap>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FranceMap],
    }).compileComponents();

    fixture = TestBed.createComponent(FranceMap);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
