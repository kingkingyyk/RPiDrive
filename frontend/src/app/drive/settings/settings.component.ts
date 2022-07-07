import { MediaMatcher } from '@angular/cdk/layout';
import { ChangeDetectorRef, Component, Inject, Input, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatMenuTrigger } from '@angular/material/menu';
import { MatSidenav } from '@angular/material/sidenav';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { Title } from '@angular/platform-browser';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonService } from 'src/app/services/common.service';
import { GetUsersResponse, NetworkUsage, SystemInfo, User } from '../models';
import { Url } from '../urls';

class SettingType {
  name: string;
  url: string;

  constructor(n: string, u: string) {
    this.name = n;
    this.url = u;
  }
}
@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements OnInit, OnDestroy {
  mobileQuery: MediaQueryList;
  private _mobileQueryListener: any;
  @ViewChild(MatSidenav) snav: MatSidenav;

  loading: boolean = false;
  errorText: string;

  settingsType: string = '';
  components: SettingType[] = [];

  constructor(private service: CommonService,
    private router: Router,
    private route: ActivatedRoute,
    private titleService: Title,
    private media: MediaMatcher,
    private changeDetectorRef: ChangeDetectorRef) {

    // Responsive sidenav
    this.mobileQuery = this.media.matchMedia('(max-width: 600px)');
    this._mobileQueryListener = () => this.changeDetectorRef.detectChanges();
    this.mobileQuery.addEventListener('change', this._mobileQueryListener);
  }

  ngOnInit(): void {
    this.titleService.setTitle('Settings - RPi Drive');
    
    if (this.route.firstChild) {
      this.settingsType = this.route.firstChild?.snapshot.params['type'];
    }

    this.components = [
      new SettingType('User Accounts', Url.getUserSettingsRelUrl()),
      new SettingType('Network Usage', Url.getNetworkSettingsRelUrl()),
      new SettingType('System', Url.getSystemSettingsRelUrl()),
    ];

    this.loading = true;
    this.errorText = null;
    this.service.getCurrentUser().subscribe( (currUser: User) => {
      if (!currUser.isSuperuser) this.errorText = 'You have no permission to access this page';
    }, error => {
      this.errorText = error.error['error'];
    }).add(() => this.loading = false);
  }

  ngOnDestroy(): void {
    this.mobileQuery.removeEventListener('change', this._mobileQueryListener);
  }

  onTabSelected(event: any): void {
    this.closeSideNavIfNeeded();
    this.router.navigate([Url.getSettingsAbsUrl() + '/' + this.settingsType]);
  }

  closeSideNavIfNeeded(): void {
    if (this.mobileQuery.matches && this.snav) this.snav.close();
  }
}

@Component({
  selector: 'app-settings-user',
  templateUrl: './user.component.html',
  styleUrls: ['./user.component.scss']
})
export class UserSettingsComponent implements OnInit {
  @Input() isMobile: boolean;

  users: User[];
  loading: boolean = false;
  errorText: string = '';

  displayedColumns: string[] = ['isActive', 'username', 'name', 'email', 'isSuperuser', 'lastLogin'];
  dataSource: MatTableDataSource<User>;
  @ViewChild(MatSort, { static: false }) set sort(_sort: MatSort) {
    this.dataSource.sort = _sort;
  }

  @ViewChild(MatMenuTrigger) contextMenu: MatMenuTrigger;
  contextMenuPosition = { x: '0px', y: '0px' };

  constructor(private service: CommonService,
    private titleService: Title,
    private snackBar: MatSnackBar,
    private dialog: MatDialog) {
    this.titleService.setTitle('User Accounts - Settings - RPi Drive');
    this.dataSource = new MatTableDataSource();
  }

  ngOnInit() {
    this.loadUsers();
  }

  onContextMenu(event: MouseEvent, item: User) {
    event.preventDefault();
    this.contextMenuPosition.x = event.clientX + 'px';
    this.contextMenuPosition.y = event.clientY + 'px';
    this.contextMenu.menuData = { 'item': item };
    this.contextMenu.menu.focusFirstItem('mouse');
    this.contextMenu.openMenu();
  }

  loadUsers() {
    this.loading = true;
    this.service.getUsers().subscribe((data: GetUsersResponse) => {
      this.users = data.values;
      this.dataSource.data = this.users;
    }, error => {
      this.errorText = error.error['error'];
    }).add(() => this.loading = false);
  }

  createUser() {
    const dialogRef = this.dialog.open(EditUserComponent, {
      disableClose: true
    });
    dialogRef.afterClosed().subscribe((data: any) => {
      if (data) this.loadUsers();
    })
  }

  editUser(user: User) {
    const dialogRef = this.dialog.open(EditUserComponent, {
      disableClose: true,
      data: user
    });
    dialogRef.afterClosed().subscribe((data: any) => {
      if (data) this.loadUsers();
    })
  }

  deleteUser(user: User) {
    const dialogRef = this.dialog.open(DeleteUserComponent, {
      disableClose: true,
      data: user
    });
    dialogRef.afterClosed().subscribe((data: any) => {
      if (data) this.loadUsers();
    })
  }
}

@Component({
  selector: 'app-settings-edit-user',
  templateUrl: './edit-user.component.html',
  styleUrls: ['./edit-user.component.scss']
})
export class EditUserComponent implements OnInit {
  loading: boolean = false;
  errorText: string = '';
  formGroup: UntypedFormGroup;
  passwordPlaceholder: string = 'THIS IS A PASSWORD';

  constructor(private service: CommonService,
    private dialogRef: MatDialogRef<EditUserComponent>,
    @Inject(MAT_DIALOG_DATA) public user: User,
    private formBuilder: UntypedFormBuilder) { }

  ngOnInit() {
    let usernameValue = '';
    let passwordValue = '';
    let confirmPasswordValue = '';
    let firstNameValue = '';
    let lastNameValue = '';
    let emailValue = '';
    let isActiveValue = true;
    let isSuperuserValue = false;

    if (this.user) {
      usernameValue = this.user.username;
      passwordValue = this.passwordPlaceholder;
      confirmPasswordValue = this.passwordPlaceholder;
      firstNameValue = this.user.firstName;
      lastNameValue = this.user.lastName;
      emailValue = this.user.email;
      isActiveValue = this.user.isActive;
      isSuperuserValue = this.user.isSuperuser;
    }

    this.formGroup = this.formBuilder.group({
      username: [usernameValue, Validators.required],
      password: [passwordValue, Validators.required],
      confirmPassword: [confirmPasswordValue, Validators.required],
      firstName: [firstNameValue],
      lastName: [lastNameValue],
      email: [emailValue, [Validators.required, Validators.email]],
      isActive: [isActiveValue, Validators.required],
      isSuperuser: [isSuperuserValue, Validators.required],
    });
  }

  private formToUser(): any {
    let formData = this.formGroup.value;
    let ret = {
      'username': formData['username'],
      'password': formData['password'],
      'firstName': formData['firstName'],
      'lastName': formData['lastName'],
      'email': formData['email'],
      'isActive': formData['isActive'],
      'isSuperuser': formData['isSuperuser'],
    }
    if (ret['password'] === this.passwordPlaceholder) ret['password'] = null;
    return ret;
  }

  createOrUpdate() {
    this.loading = true;
    if (this.user) {
      this.service.updateUser(this.user.id, this.formToUser()).subscribe(() => {
        this.dialogRef.close(1);
      }, error => {
        this.errorText = error.error['error'];
      }).add(() => this.loading = false);
    } else {
      this.service.createUser(this.formToUser()).subscribe(() => {
        this.dialogRef.close(1);
      }, error => {
        this.errorText = error.error['error'];
      }).add(() => this.loading = false);
    }
  }
}

@Component({
  selector: 'app-settings-delete-user',
  templateUrl: './delete-user.component.html',
})
export class DeleteUserComponent {
  loading: boolean = false;
  errorText: string = '';

  constructor(private service: CommonService,
    private dialogRef: MatDialogRef<DeleteUserComponent>,
    @Inject(MAT_DIALOG_DATA) public user: User) { }

  delete() {
    this.loading = true;
    this.service.deleteUser(this.user.id).subscribe(() => {
      this.dialogRef.close(1);
    }, error => {
      this.errorText = error.error['error'];
    }).add(() => this.loading = false);
  }
}


@Component({
  selector: 'app-settings-network',
  templateUrl: './network.component.html'
})
export class NetworkSettingsComponent implements OnInit, OnDestroy {
  timer: any;
  currData: NetworkUsage;

  constructor(private service: CommonService,
    private titleService: Title,
    private snackBar: MatSnackBar) {
    this.titleService.setTitle('Network Usage - Settings - RPi Drive')
  }

  ngOnInit() {
    this.loadData();
    this.timer = setInterval(() => this.loadData(), 3000);
  }

  ngOnDestroy() {
    if (this.timer) clearInterval(this.timer);
  }

  loadData() {
    this.service.getNetworkUsage().subscribe((data: NetworkUsage) => {
      this.currData = data;
    });
  }
}

@Component({
  selector: 'app-settings-system',
  templateUrl: './system.component.html'
})
export class SystemSettingsComponent implements OnInit {
  timer: any;
  currData: SystemInfo;

  constructor(private service: CommonService,
    private titleService: Title,
    private snackBar: MatSnackBar) {
    this.titleService.setTitle('System - Settings - RPi Drive')
  }

  ngOnInit() {
    this.loadData();
    this.timer = setInterval(() => this.loadData(), 3000);
  }

  ngOnDestroy() {
    if (this.timer) clearInterval(this.timer);
  }
  loadData() {
    this.service.getSystemInfo().subscribe((data: SystemInfo) => {
      this.currData = data;
    });
  }
}