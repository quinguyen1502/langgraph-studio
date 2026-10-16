import { LogOut, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { getUser, logout } from '@/lib/api'

export function UserMenu() {
  const u = getUser()
  return <DropdownMenu>
    <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" className="rounded-full" id="user-menu">
      <Avatar className="size-7"><AvatarFallback className="text-xs">{(u?.email || '?')[0].toUpperCase()}</AvatarFallback></Avatar></Button></DropdownMenuTrigger>
    <DropdownMenuContent align="end" className="w-56">
      <DropdownMenuLabel className="flex items-center gap-2 font-normal"><User className="size-4" />{u?.email}</DropdownMenuLabel>
      <DropdownMenuSeparator />
      <DropdownMenuItem onClick={logout}><LogOut />Đăng xuất</DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
}
