from api.urls import router
from accounts.views import *


router.register('users', UserViewSet, basename='user')
router.register('squads', SquadViewSet, basename='squad')
router.register('departments', DepartmentViewSet, basename='department')
router.register('branches', BranchViewSet, basename='branch')
router.register('addresses', AddressViewSet, basename='address')
router.register('roles', RoleViewSet, basename='role')
router.register('permissions', PermissionViewSet, basename='permission')
router.register('groups', GroupViewSet, basename='group')
router.register('employees', EmployeeViewSet, basename='employee')