from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from .models import User, Department, Employee, Role, Branch, Address, PhoneNumber, Squad, UserType
from accounts.serializers import UserSerializer, DepartmentSerializer, EmployeeSerializer


class UserTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='test', 
            email='test@example.com', 
            password='testpass', 
            complete_name='Test User'
        )
        self.url = reverse('api:user-list')
        self.user_type, created = UserType.objects.get_or_create(
            name='Funcionário', 
            defaults={'description': 'Funcionário da empresa'}
        )
        self.address = Address.objects.create(
            zip_code='12345678',
            country='Brazil',
            state='PA',
            city='Belém',
            neighborhood='Barreiro',
            street='Passagem Boa Fé',
            number='123'
        )

    def test_list_users(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_superuser(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "email": "super@example.com",
            "username": "superuser",
            "complete_name": "Super User",
            "user_types_ids": [self.user_type.id],
            "addresses_ids": [self.address.id],
            "groups_ids": [],
            "phone_numbers_ids": []
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(
            email="super@example.com", 
            username="superuser"
        ).exists())


class DepartmentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin', 
            email='admin@example.com', 
            password='testpass', 
            complete_name='Admin User'
        )
        self.owner = User.objects.create_user(
            username='ownerdept',
            email='ownerdept@example.com',
            password='testpass',
            complete_name='Owner Dept'
        )
        self.department = Department.objects.create(
            name='Tecnologia',
            email='ti@example.com',
            owner=self.owner
        )

        self.client.force_authenticate(user=self.user)
        self.url = reverse('api:department-list')

    def test_list_departments(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Tecnologia', response.content.decode())

    def test_create_department(self):
        data = {
            "name": "Financeiro",
            "email": "financeiro@example.com",
            "owner_id": self.owner.id
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Department.objects.filter(
            name="Financeiro",
            email="financeiro@example.com"
        ).exists())


class EmployeeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='manager', email='manager@example.com', password='testpass', complete_name='Manager User')
        self.address = Address.objects.create(
            zip_code='12345678',
            country='Brazil',
            state='SP',
            city='São Paulo',
            neighborhood='Centro',
            street='Rua A',
            number='123'
        )
        self.branch = Branch.objects.create(name='Main', address=self.address)
        self.owner = User.objects.create_user(
            username='ownerit',
            email='ownerit@example.com',
            password='testpass',
            complete_name='Owner IT'
        )
        self.department = Department.objects.create(name='IT', owner=self.owner)
        self.role = Role.objects.create(name='Developer')
        self.url = reverse('api:employee-list')

    def test_list_employees(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_employee(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "user_id": self.user.id,
            "contract_type": "C",
            "branch_id": self.branch.id,
            "department_id": self.department.id,
            "role_id": self.role.id,
            "user_manager_id": self.owner.id,
            "hire_date": "2024-01-01"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Employee.objects.filter(user=self.user).exists())


class BranchTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='owner', email='owner@example.com', password='testpass', complete_name='Owner User')
        self.address = Address.objects.create(zip_code='12345', country='Country', state='State', city='City', neighborhood='Downtown', street='Street', number='100')
        self.branch = Branch.objects.create(name='Main', address=self.address)
        
        self.client.force_authenticate(user=self.user)
        self.url = reverse('api:branch-list')

    def test_create_branch(self):
        data = {
            "name": "New Branch",
            "address_id": self.address.id,
            "owners_ids": [self.user.id]
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Branch.objects.filter(name="New Branch").exists())


class SquadTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='squadowner', 
            email='squadowner@example.com', 
            password='testpass', 
            complete_name='Squad Owner'
        )
        self.member1 = User.objects.create_user(
            username='member1',
            email='member1@example.com',
            password='testpass',
            complete_name='Member One'
        )
        self.member2 = User.objects.create_user(
            username='member2',
            email='member2@example.com',
            password='testpass',
            complete_name='Member Two',
        )
        self.address = Address.objects.create(
            zip_code='12345',
            country='Country',
            state='State',
            city='City',
            neighborhood='Downtown',
            street='Street',
            number='100'
        )
        self.branch = Branch.objects.create(name='BranchX', address=self.address)
        self.branch.owners.set([self.user])
        self.url = reverse('api:squad-list')

    def test_list_squads(self):
        squad = Squad.objects.create(
            name="Team Alpha",
            branch=self.branch,
            manager=self.user
        )
        squad.members.set([self.member1, self.member2])
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Team Alpha", response.content.decode())

    def test_create_squad(self):
        data = {
            "name": "Team Beta",
            "branch_id": self.branch.id,
            "manager_id": self.user.id,
            "members_ids": [self.member1.id, self.member2.id]
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Squad.objects.filter(name="Team Beta", branch=self.branch, manager=self.user).exists())
        squad = Squad.objects.get(name="Team Beta")
        self.assertEqual(squad.members.count(), 2)
        self.assertIn(self.member1, squad.members.all())
        self.assertIn(self.member2, squad.members.all())


class AddressTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='addruser', email='addruser@example.com', password='testpass', complete_name='Address User')
        self.url = reverse('api:address-list')

    def test_create_address(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "zip_code": "99999999",
            "country": "Brazil",
            "state": "SP",
            "city": "São Paulo",
            "neighborhood": "Bela Vista",
            "street": "Av. Paulista",
            "number": "100"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class PhoneNumberTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='phoneuser', 
            email='phoneuser@example.com', 
            password='testpass', 
            complete_name='Phone User'
        )
        self.url = reverse('api:phone_number-list')

    def test_create_phone_number(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "country_code": 55,
            "area_code": "12",
            "phone_number": "123456789",
            "is_main": True,
            "user_id": self.user.id
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PhoneNumber.objects.filter(
            country_code=55, 
            area_code="12", 
            phone_number="123456789",
            user=self.user
        ).exists())


class RoleTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='roleuser', email='roleuser@example.com', password='testpass', complete_name='Role User')
        self.url = reverse('api:role-list')

    def test_create_role(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "name": "Tester"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Role.objects.filter(name="Tester").exists())


class PermissionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='permuser', email='permuser@example.com', password='testpass', complete_name='Perm User')
        self.url = reverse('api:permission-list')
        # Crie um ContentType para testar
        from django.contrib.contenttypes.models import ContentType
        self.ct = ContentType.objects.create(app_label='testapp', model='testmodel')

    def test_create_permission(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "name": "Can Test",
            "codename": "can_test",
            "content_type_id": self.ct.id
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class GroupTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='groupuser', email='groupuser@example.com', password='testpass', complete_name='Group User')
        self.url = reverse('api:group-list')
        # Crie uma Permission para testar
        self.ct = ContentType.objects.create(app_label='testapp2', model='testmodel2')
        self.permission = Permission.objects.create(name="Can Manage", codename="can_manage", content_type=self.ct)

    def test_create_group(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "name": "GroupTest",
            "permissions_ids": [self.permission.id]
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
