import { setupTestingRouter } from "@angular/router/testing";

export abstract class Url {
    public static getRootURL(): string {
        return 'drive';
    }
    public static getSetupRelURL(): string {
        return 'setup';
    }
    public static getSetupAbsURL(): string {
        return this.getRootURL() + '/' + this.getSetupRelURL();
    }
    public static getLoginRelURL(): string {
        return 'login';
    }
    public static getLoginAbsURL(): string {
        return this.getRootURL() + '/' + this.getLoginRelURL();
    }
    public static getFolderRelURL(): string {
        return 'folder';
    }
    public static getFolderAbsURL(): string {
        return this.getRootURL() + '/' + this.getFolderRelURL();
    }
}
