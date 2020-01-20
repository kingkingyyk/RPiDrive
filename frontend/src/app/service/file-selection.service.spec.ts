import { TestBed } from '@angular/core/testing';

import { FileSelectionService } from './file-selection.service';

describe('FileSelectionService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: FileSelectionService = TestBed.get(FileSelectionService);
    expect(service).toBeTruthy();
  });
});
