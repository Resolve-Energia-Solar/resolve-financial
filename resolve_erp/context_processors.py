def menu_items(request):
    items = [
        # CRM Section
        {
            "label": "Dashboard",
            "url_name": "core:index",
            "icon": "bx bx-bar-chart",
            "permission": "core.view_dashboard"
        },
        {
            "label": "Fluxo",
            "icon": "bx bx-chevrons-right",
            "permission": "core.view_board",
            "sub_items": [
                {
                    "label": "Board Detail",
                    "url_static": "#",
                    "permission": "core.view_board"
                }
            ]
        },
        {
            "label": "Leads",
            "icon": "bx bx-user",
            "permission": "resolve_crm.view_lead",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "resolve_crm:lead_list",
                    "permission": "resolve_crm.view_lead"
                },
                {
                    "label": "Criar",
                    "url_name": "resolve_crm:lead_create",
                    "permission": "resolve_crm.add_lead"
                }
            ]
        },
        {
            "label": "Atividades",
            "icon": "bx bx-objects-vertical-top",
            "permission": "resolve_crm.view_task",
            "sub_items": [
                {
                    "label": "Tarefas",
                    "url_name": "resolve_crm:tasks",
                    "permission": "resolve_crm.view_task"
                }
            ]
        },
        # Portal do Vendedor Section
        {
            "label": "Portal do Vendedor",
            "icon": "bx bx-layout",
            "permission": "portal.view_vendor",
            "sub_items": [
                {
                    "label": "Meus clientes",
                    "url_static": "sneat-template/html/vertical-menu-template/layouts-collapsed-menu.html",
                    "permission": "portal.view_client"
                },
                {
                    "label": "Minhas vendas",
                    "url_static": "layouts-content-navbar.html",
                    "permission": "portal.view_sales"
                },
                {
                    "label": "Minhas vistorias",
                    "url_static": "layouts-content-navbar.html",
                    "permission": "portal.view_inspections"
                }
            ]
        },
        # Administração Section
        {
            "label": "Administração",
            "header": True
        },
        {
            "label": "Usuários",
            "icon": "bx bx-user",
            "permission": "accounts.view_user",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "accounts:users_list",
                    "permission": "accounts.view_user"
                },
                {
                    "label": "Criar",
                    "url_name": "accounts:user_create",
                    "permission": "accounts.add_user"
                }
            ]
        },
        {
            "label": "Squads",
            "icon": "bx bx-group",
            "permission": "accounts.view_squad",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "accounts:squad_list",
                    "permission": "accounts.view_squad"
                },
                {
                    "label": "Criar",
                    "url_name": "accounts:squad_create",
                    "permission": "accounts.add_squad"
                }
            ]
        },
        {
            "label": "Unidades",
            "icon": "bx bx-building",
            "permission": "accounts.view_branch",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "accounts:branch_list",
                    "permission": "accounts.view_branch"
                },
                {
                    "label": "Criar",
                    "url_name": "accounts:branch_create",
                    "permission": "accounts.add_branch"
                }
            ]
        },
        {
            "label": "Quadros",
            "icon": "bx bx-objects-vertical-top",
            "permission": "core.view_board",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "core:board-list",
                    "permission": "core.view_board"
                },
                {
                    "label": "Criar",
                    "url_name": "core:board-create",
                    "permission": "core.add_board"
                }
            ]
        },
        {
            "label": "Perfis",
            "icon": "bx bx-group",
            "permission": "accounts.view_group",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "accounts:group_list",
                    "permission": "accounts.view_group"
                },
                {
                    "label": "Criar",
                    "url_name": "accounts:group_create",
                    "permission": "accounts.add_group"
                }
            ]
        },
        {
            "label": "Permissões",
            "icon": "bx bx-key",
            "permission": "accounts.view_permission",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "accounts:permission_list",
                    "permission": "accounts.view_permission"
                },
                {
                    "label": "Criar",
                    "url_name": "accounts:permission_create",
                    "permission": "accounts.add_permission"
                }
            ]
        },
        {
            "label": "Endereços",
            "icon": "bx bx-map",
            "permission": "accounts.view_address",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "accounts:address_list",
                    "permission": "accounts.view_address"
                },
                {
                    "label": "Criar",
                    "url_name": "accounts:address_create",
                    "permission": "accounts.add_address"
                }
            ]
        },
        {
            "label": "Setores",
            "icon": "bx bx-shape-square",
            "permission": "accounts.view_department",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "accounts:department_list",
                    "permission": "accounts.view_department"
                },
                {
                    "label": "Criar",
                    "url_name": "accounts:department_create",
                    "permission": "accounts.add_department"
                }
            ]
        },
        {
            "label": "Cargos",
            "icon": "bx bxs-user-detail",
            "permission": "accounts.view_role",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "accounts:role_list",
                    "permission": "accounts.view_role"
                },
                {
                    "label": "Criar",
                    "url_name": "accounts:role_create",
                    "permission": "accounts.add_role"
                }
            ]
        },
        # Misc Section
        {
            "label": "Miscelânea",
            "header": True
        },
        {
            "label": "Suporte",
            "icon": "bx bx-support",
            "url_static": "https://resolveenergiasolar.com.br/support/",
            "permission": "misc.view_support"
        },
        {
            "label": "Tutoriais",
            "icon": "bx bx-file",
            "url_static": "https://demos.themeselection.com/sneat-bootstrap-html-admin-template/documentation/",
            "permission": "misc.view_tutorials"
        }
    ]
    return {'menu_items': items}