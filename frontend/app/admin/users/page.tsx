// frontend/app/admin/users/page.tsx
'use client';

import { useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { getAllUsers, updateUserRole, toggleUserActive, User } from '@/lib/authApi';
import { Search, Users, Crown, User as UserIcon, RefreshCw, Lock, Unlock } from 'lucide-react';

// 格式化相对时间
function formatTime(dateStr?: string | null) {
  if (!dateStr) return '从未登录';
  const date = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (diff < 60) return '刚刚';
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
  if (diff < 2592000) return `${Math.floor(diff / 86400)}天前`;
  return date.toLocaleDateString('zh-CN');
}

// 格式化完整时间
function formatFullTime(dateStr?: string | null) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

const ITEMS_PER_PAGE = 10;

export default function AdminUsersPage() {
  const router = useRouter();
  const { user, token, isAdmin, isLoading } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  // 权限校验：非管理员跳转首页
  useEffect(() => {
    if (!isLoading && !isAdmin) {
      router.push('/');
    }
  }, [isAdmin, isLoading, router]);

  // 加载用户列表
  useEffect(() => {
    if (!isAdmin || !token) return;
    const fetchUsers = async () => {
      try {
        const data = await getAllUsers(token);
        setUsers(data);
      } catch (err) {
        setError('加载用户列表失败');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchUsers();
  }, [isAdmin, token]);

  // 搜索过滤
  const filteredUsers = useMemo(() => {
    if (!searchTerm.trim()) return users;
    return users.filter(u =>
      u.username.toLowerCase().includes(searchTerm.trim().toLowerCase())
    );
  }, [users, searchTerm]);

  // 分页
  const totalPages = Math.ceil(filteredUsers.length / ITEMS_PER_PAGE);
  const paginatedUsers = filteredUsers.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  // 统计数据
  const stats = {
    total: users.length,
    admin: users.filter(u => u.role === 'admin').length,
    user: users.filter(u => u.role === 'user').length,
    active: users.filter(u => u.is_active !== false).length,
    inactive: users.filter(u => u.is_active === false).length,
  };

  // 切换角色
  const handleToggleRole = async (targetUser: User) => {
    if (!token) return;
    const newRole = targetUser.role === 'admin' ? 'user' : 'admin';

    if (targetUser.role === 'admin' && users.filter(u => u.role === 'admin').length <= 1) {
      setError('⚠️ 系统至少需要保留一个管理员');
      return;
    }

    setUpdating(targetUser.id);
    setError('');
    setSuccess('');
    try {
      const updated = await updateUserRole(token, targetUser.id, newRole);
      setUsers(prev => prev.map(u => u.id === updated.id ? { ...u, ...updated } : u));
      setSuccess(`✅ 用户「${targetUser.username}」已${newRole === 'admin' ? '提升为管理员' : '降级为普通用户'}`);
    } catch (err) {
      setError('操作失败，请重试');
    } finally {
      setUpdating(null);
    }
  };

  // 禁用/启用用户
  const handleToggleActive = async (targetUser: User) => {
    if (!token) return;
    if (targetUser.id === user?.id) {
      setError('⚠️ 不能禁用自己');
      return;
    }

    setUpdating(targetUser.id);
    setError('');
    setSuccess('');
    try {
      const updated = await toggleUserActive(token, targetUser.id);
      setUsers(prev => prev.map(u => u.id === updated.id ? { ...u, ...updated } : u));
      setSuccess(`✅ 用户「${targetUser.username}」已${updated.is_active ? '启用' : '禁用'}`);
    } catch (err) {
      setError('操作失败，请重试');
    } finally {
      setUpdating(null);
    }
  };

  // 刷新列表
  const handleRefresh = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await getAllUsers(token);
      setUsers(data);
      setSuccess('✅ 已刷新');
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError('刷新失败');
    } finally {
      setLoading(false);
    }
  };

  if (isLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-[#6a6a7e]">加载中...</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* 标题 + 刷新按钮 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[#1a1a2e]">👥 用户管理</h1>
          <p className="text-sm text-[#6a6a7e]">管理所有注册用户，可以提升/降级管理员权限，或禁用/启用账号</p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 rounded-xl border border-[#e8e8ea] text-sm text-[#6a6a7e] hover:bg-[#f0f0f5] transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        <div className="bg-white rounded-2xl border border-[#e8e8ea] p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-50 text-blue-600">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-[#1a1a2e]">{stats.total}</div>
              <div className="text-xs text-[#6a6a7e]">总用户</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-2xl border border-[#e8e8ea] p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-purple-50 text-purple-600">
              <Crown className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-[#1a1a2e]">{stats.admin}</div>
              <div className="text-xs text-[#6a6a7e]">管理员</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-2xl border border-[#e8e8ea] p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gray-50 text-gray-600">
              <UserIcon className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-[#1a1a2e]">{stats.user}</div>
              <div className="text-xs text-[#6a6a7e]">普通用户</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-2xl border border-[#e8e8ea] p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-green-50 text-green-600">
              <Unlock className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-[#1a1a2e]">{stats.active}</div>
              <div className="text-xs text-[#6a6a7e]">已启用</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-2xl border border-[#e8e8ea] p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-red-50 text-red-600">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-[#1a1a2e]">{stats.inactive}</div>
              <div className="text-xs text-[#6a6a7e]">已禁用</div>
            </div>
          </div>
        </div>
      </div>

      {/* 消息提示 */}
      {error && (
        <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 p-3 rounded-xl bg-green-50 border border-green-200 text-green-600 text-sm">
          {success}
        </div>
      )}

      {/* 搜索框 */}
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8a8a9e]" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            placeholder="搜索用户名..."
            className="w-full h-11 pl-10 pr-4 rounded-xl border border-[#e8e8ea] bg-white text-sm outline-none focus:border-[#4f46e5] focus:ring-4 focus:ring-indigo-100 transition-all"
          />
        </div>
      </div>

      {/* 用户表格 */}
      <div className="bg-white rounded-2xl border border-[#e8e8ea] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[800px]">
            <thead className="bg-[#f8f8fa] border-b border-[#e8e8ea]">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-[#6a6a7e] uppercase tracking-wider">ID</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-[#6a6a7e] uppercase tracking-wider">用户名</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-[#6a6a7e] uppercase tracking-wider">角色</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-[#6a6a7e] uppercase tracking-wider">状态</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-[#6a6a7e] uppercase tracking-wider">注册时间</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-[#6a6a7e] uppercase tracking-wider">最后登录</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-[#6a6a7e] uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f0f0f5]">
              {paginatedUsers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-sm text-[#6a6a7e]">
                    {searchTerm ? '没有匹配的用户' : '暂无用户'}
                  </td>
                </tr>
              ) : (
                paginatedUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-[#f8f8fa] transition-colors">
                    <td className="px-4 py-3 text-sm text-[#1a1a2e]">#{u.id}</td>
                    <td className="px-4 py-3 text-sm font-medium text-[#1a1a2e]">
                      {u.username}
                      {u.id === user?.id && (
                        <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-[#f0f0ff] text-[#4f46e5]">
                          你
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        u.role === 'admin'
                          ? 'bg-purple-50 text-purple-700'
                          : 'bg-gray-50 text-gray-600'
                      }`}>
                        {u.role === 'admin' ? '👑 管理员' : '👤 用户'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        u.is_active !== false
                          ? 'bg-green-50 text-green-700'
                          : 'bg-red-50 text-red-700'
                      }`}>
                        {u.is_active !== false ? '✅ 启用' : '❌ 禁用'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-[#6a6a7e]">
                      {formatFullTime(u.created_at)}
                    </td>
                    <td className="px-4 py-3 text-sm text-[#6a6a7e]">
                      {formatTime(u.last_login_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {/* 角色切换按钮 */}
                        <button
                          onClick={() => handleToggleRole(u)}
                          disabled={updating === u.id || u.id === user?.id}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                            u.role === 'admin'
                              ? 'bg-orange-50 text-orange-600 hover:bg-orange-100'
                              : 'bg-[#4f46e5] text-white hover:bg-[#4338ca]'
                          } disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap`}
                        >
                          {updating === u.id ? '...' : (u.role === 'admin' ? '降级' : '提升')}
                        </button>
                        {/* 禁用/启用按钮 */}
                        {u.id !== user?.id && (
                          <button
                            onClick={() => handleToggleActive(u)}
                            disabled={updating === u.id}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                              u.is_active !== false
                                ? 'bg-red-50 text-red-600 hover:bg-red-100'
                                : 'bg-green-50 text-green-600 hover:bg-green-100'
                            } disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap`}
                          >
                            {updating === u.id ? '...' : (u.is_active !== false ? '禁用' : '启用')}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 底部统计 + 分页 */}
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-[#6a6a7e]">
        <div>
          共 {filteredUsers.length} 位用户
          {searchTerm && `（搜索: "${searchTerm}"）`}
        </div>
        {totalPages > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 rounded-lg border border-[#e8e8ea] hover:bg-[#f0f0f5] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              上一页
            </button>
            <span className="px-3 py-1">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 rounded-lg border border-[#e8e8ea] hover:bg-[#f0f0f5] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              下一页
            </button>
          </div>
        )}
      </div>
    </div>
  );
}