from django.urls import reverse

def menu_items(request):
    items = [
        # CRM Section
        {
            "label": "Dashboard",
            "url_name": "core:index",
            "icon": "bx bx-bar-chart",
            "permission": "core.view_dashboard",
            "section": "CRM"
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
            ],
            "section": "CRM"
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
            ],
            "section": "CRM"
        },
        # Administração Section
        {
            "label": "Usuários",
            "icon": "bx bx-user",
            "permission": "accounts.view_user",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "accounts:user_list",
                    "permission": "accounts.view_user"
                },
                {
                    "label": "Criar",
                    "url_name": "accounts:user_create",
                    "permission": "accounts.add_user"
                }
            ],
            "section": "Administração"
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
            ],
            "section": "Administração"
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
            ],
            "section": "Administração"
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
            ],
            "section": "Administração"
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
            ],
            "section": "Administração"
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
            ],
            "section": "Administração"
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
            ],
            "section": "Administração"
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
            ],
            "section": "Administração"
        },
        {
            "label": "Cargos",
            "icon": "bx bxs-user-detail",
            "permission": "accounts.view_role",
            "section": "Administração",
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
        {
            "label": "Campanhas",
            "icon": "bx bx-star",
            "section": "Administração",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "resolve_crm:campaign_list",
                    "permission": "resolve_crm.view_marketingcampaign"
                },
                {
                    "label": "Criar",
                    "url_name": "resolve_crm:campaign_create",
                    "permission": "resolve_crm.add_marketingcampaign"
                }
            ]
        },
        {
            "label": "Perfis",
            "icon": "bx bx-group",
            "section": "Administração",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "accounts:group_list",
                    "permission": "auth.view_group"
                },
                {
                    "label": "Criar",
                    "url_name": "accounts:group_create",
                    "permission": "auth.add_group"
                }
            ]
        },
        {
            "label": "Permissões",
            "icon": "bx bx-key",
            "section": "Administração",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "accounts:permission_list",
                    "permission": "auth.view_permission"
                },
                {
                    "label": "Criar",
                    "url_name": "accounts:permission_create",
                    "permission": "auth.add_permission"
                }
            ]
        },
        {
            "label": "Financiadoras",
            "icon": "bx bx-dollar",
            "section": "Administração",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "resolve_crm:financier_list",
                    "permission": "resolve_crm.view_financier"
                },
                {
                    "label": "Criar",
                    "url_name": "engineering:circuitbreaker_create",
                    "permission": "engineering.add_circuitbreaker"
                }
            ]
        },
        {
            "label": "Materiais",
            "icon": "bx bx-package",
            "section": "Logística",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "logistics:materials_list",
                    "permission": "logistics.view_materials"
                },
                {
                    "label": "Criar",
                    "url_name": "logistics:materials_create",
                    "permission": "logistics.add_materials"
                }
            ]
        },
        {
            "label": "Tipos de Materiais",
            "icon": "bx bx-collection",
            "section": "Logística",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "logistics:material_type_list",
                    "permission": "logistics.view_materialtypes"
                },
                {
                    "label": "Criar",
                    "url_name": "logistics:material_type_create",
                    "permission": "logistics.add_materialtypes"
                }
            ]
        },
        {
            "label": "Tipos de Telhado",
            "icon": "bx bxs-up-arrow",
            "section": "Vistoria",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "inspections:roof_type_list",
                    "permission": "inspections.view_rooftype"
                },
                {
                    "label": "Criar",
                    "url_name": "inspections:roof_type_create",
                    "permission": "inspections.add_rooftype"
                }
            ]
        },
        {
            "label": "Disjuntores",
            "icon": "bx bx-plug",
            "section": "Engenharia",
            "sub_items": [
                {
                    "label": "Lista",
                    "url_name": "engineering:circuitbreaker_list",
                    "permission": "engineering.view_circuitbreaker"
                },
                {
                    "label": "Criar",
                    "url_name": "engineering:circuitbreaker_create",
                    "permission": "engineering.add_circuitbreaker"
                }
            ]
        }
    ]

    current_path = request.path

    # Filtra os itens baseados nas permissões e atualiza os URLs
    filtered_items = []
    sections = {}

    for item in items:
        item['active'] = False
        if 'sub_items' in item:
            visible_sub_items = []
            for sub_item in item['sub_items']:
                sub_item['url'] = reverse(sub_item['url_name'])
                if sub_item.get('permission') in request.user.get_all_permissions():
                    visible_sub_items.append(sub_item)
                    if sub_item['url'] == current_path:
                        item['active'] = True
                        sub_item['active'] = True
                    else:
                        sub_item['active'] = False
            item['sub_items'] = visible_sub_items
            if visible_sub_items:
                filtered_items.append(item)
        else:
            item['url'] = reverse(item['url_name']) if 'url_name' in item else None
            if item.get('permission') in request.user.get_all_permissions():
                filtered_items.append(item)
                if item['url'] == current_path:
                    item['active'] = True
            elif 'header' in item:
                filtered_items.append(item)

    # Agrupa os itens por seção
    for item in filtered_items:
        section = item['section']
        if section not in sections:
            sections[section] = []
        sections[section].append(item)

    # Retorna as seções com seus respectivos itens visíveis
    return {'menu_items': sections}