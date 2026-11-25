export interface UsuarioAutenticado {
  codigo: string
  matricula: string
  nome: string
  email: string
  telefone: string | null
  papel: 'LEITOR' | 'BIBLIOTECARIO'
  ativo: boolean
}

export type EstadoAutenticacao =
  | 'checking'
  | 'authenticated'
  | 'unauthenticated'
  | 'error'
