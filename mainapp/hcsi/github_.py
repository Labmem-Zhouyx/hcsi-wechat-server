from github import Github


def invite_user(username, GithubConfig):
    g = Github(login_or_token=GithubConfig.access_token)
    # 验证用户是否存在
    try:
        user = g.get_user(username)
    except:
        mini_program_subject = '用户名不存在'
        mini_program_text = f'Github用户名 {username} 不存在。'
        result_dict = {'email': {},
                       'mini_program': {'subject': mini_program_subject,
                                        'text': mini_program_text}}
        return result_dict

    # 验证组织是否存在
    try:
        organization = g.get_organization(GithubConfig.organization_name)
    except:
        mini_program_subject = '组织不存在'
        mini_program_text = f'Github组织 {GithubConfig.organization_name} 不存在。'
        result_dict = {'email': {},
                       'mini_program': {'subject': mini_program_subject,
                                        'text': mini_program_text}}
        return result_dict
    # 邀请用户
    try:
        organization.invite_user(user)
    except:
        mini_program_subject = '邀请失败'
        mini_program_text = f'Github用户 {username} 邀请失败。'
        result_dict = {'email': {},
                       'mini_program': {'mini_program_subject': mini_program_subject,
                                        'mini_program_text': mini_program_text}}
        return result_dict
    # 邀请成功，返回成功信息
    mini_program_subject = '邀请成功'
    mini_program_text = f'Github用户 {username} 邀请成功，请注意查收邮件。'
    result_dict = {'email': {},
                   'mini_program': {'mini_program_subject': mini_program_subject,
                                    'mini_program_text': mini_program_text}}
    return result_dict


def remove_user(username, GithubConfig):
    g = Github(login_or_token=GithubConfig.access_token)
    # 验证用户是否存在
    try:
        user = g.get_user(username)
    except:
        mini_program_subject = '用户名不存在'
        mini_program_text = f'Github用户名 {username} 不存在。'
        result_dict = {'email': {},
                       'mini_program': {'subject': mini_program_subject,
                                        'text': mini_program_text}}
        return result_dict

    # 验证组织是否存在
    try:
        organization = g.get_organization(GithubConfig.organization_name)
    except:
        mini_program_subject = '组织不存在'
        mini_program_text = f'Github组织 {GithubConfig.organization_name} 不存在。'
        result_dict = {'email': {},
                       'mini_program': {'subject': mini_program_subject,
                                        'text': mini_program_text}}
        return result_dict

    try:
        organization.remove_from_members(user)
    except:
        mini_program_subject = '移除失败'
        mini_program_text = f'Github用户 {username} 移除失败。'
        result_dict = {'email': {},
                       'mini_program': {'subject': mini_program_subject,
                                        'text': mini_program_text}}
        return result_dict

    mini_program_subject = '移除成功'
    mini_program_text = f'Github用户 {username} 移除成功。'
    result_dict = {'email': {},
                   'mini_program': {'mini_program_subject': mini_program_subject,
                                    'mini_program_text': mini_program_text}}
    return result_dict


if __name__ == '__main__':
    class GithubConfig:
        access_token = 'access_token'
        organization_name = 'organization_name'

    print(invite_user('username', GithubConfig))
    print(remove_user('username', GithubConfig))